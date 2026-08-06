from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from wkhtmltopdf.views import PDFTemplateResponse

from ativos.models import Ativo
from configuracoes.services import empresa_atual
from config.views import money_br, with_layout

from .forms import DevolucaoLocacaoForm, ItemLocacaoForm, ItemLocacaoFormSet, LocacaoForm
from .models import HistoricoLocacao, ItemLocacao, Locacao


PDF_OPTIONS = {
    "quiet": True,
    "encoding": "utf8",
    "enable_local_file_access": True,
}


def locacoes_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    ordem_filter = request.GET.get("ordem", "recentes").strip()
    status_validos = [status for status, _label in Locacao.Status.choices]
    ordem_options = [
        ("recentes", "Mais recentes"),
        ("antigas", "Mais antigas"),
        ("codigo", "Codigo"),
        ("cliente", "Cliente"),
        ("valor", "Maior valor"),
        ("status", "Status"),
    ]
    ordem_map = {
        "recentes": ("-data_inicio", "codigo"),
        "antigas": ("data_inicio", "codigo"),
        "codigo": ("codigo",),
        "cliente": ("cliente__nome", "codigo"),
        "valor": ("-valor_total", "codigo"),
        "status": ("status", "-data_inicio", "codigo"),
    }
    locacoes = Locacao.objects.select_related("cliente").annotate(total_itens=Count("itens"))

    if query:
        locacoes = locacoes.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    if status_filter in status_validos:
        locacoes = locacoes.filter(status=status_filter)

    if ordem_filter not in ordem_map:
        ordem_filter = "recentes"

    locacoes = list(locacoes.order_by(*ordem_map[ordem_filter]))
    for locacao in locacoes:
        locacao.valor_total_formatado = money_br(locacao.valor_total)

    status_counts = {
        "todos": Locacao.objects.count(),
        "orcamentos": Locacao.objects.filter(status=Locacao.Status.ORCAMENTO).count(),
        "ativas": Locacao.objects.filter(status=Locacao.Status.ATIVA).count(),
        "agendadas": Locacao.objects.filter(status=Locacao.Status.AGENDADA).count(),
        "finalizadas": Locacao.objects.filter(status=Locacao.Status.FINALIZADA).count(),
        "canceladas": Locacao.objects.filter(status=Locacao.Status.CANCELADA).count(),
    }

    return render(
        request,
        "locacoes/list.html",
        with_layout(
            {
                "page_title": "Locacoes",
                "locacoes": locacoes,
                "query": query,
                "status_filter": status_filter if status_filter in status_validos else "",
                "status_counts": status_counts,
                "ordem_filter": ordem_filter,
                "ordem_options": ordem_options,
            }
        ),
    )


def orcamentos_list(request):
    query = request.GET.get("q", "").strip()
    orcamentos = (
        Locacao.objects.select_related("cliente")
        .filter(status=Locacao.Status.ORCAMENTO)
        .annotate(total_itens=Count("itens"))
        .order_by("-data_inicio", "codigo")
    )

    if query:
        orcamentos = orcamentos.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    status_counts = {
        "todos": orcamentos.count(),
        "sem_itens": orcamentos.filter(total_itens=0).count(),
        "prontos": orcamentos.filter(total_itens__gt=0).count(),
    }

    return render(
        request,
        "orcamentos/list.html",
        with_layout(
            {
                "page_title": "Orcamentos",
                "orcamentos": orcamentos,
                "query": query,
                "status_counts": status_counts,
            }
        ),
    )


def locacao_create(request):
    if request.method == "POST":
        form = LocacaoForm(request.POST)
        item_formset = ItemLocacaoFormSet(request.POST, prefix="itens", form_kwargs={"require_item": False})

        if form.is_valid() and item_formset.is_valid():
            conflitos = []
            if form.cleaned_data["status"] == Locacao.Status.AGENDADA:
                conflitos = _conflitos_reserva_ativos(
                    _ativos_do_formset(item_formset),
                    form.cleaned_data["data_inicio"],
                    form.cleaned_data["data_fim"],
                )

            if conflitos:
                form.add_error(None, _mensagem_conflitos_reserva(conflitos))
            else:
                with transaction.atomic():
                    locacao = form.save()

                    for item_form in item_formset:
                        if not item_form.cleaned_data:
                            continue

                        item = item_form.save(commit=False)
                        item.locacao = locacao
                        item.save()

                    locacao.recalcular_totais()
                    _registrar_historico(
                        locacao,
                        HistoricoLocacao.Tipo.CRIACAO,
                        f"Locacao criada com {locacao.itens.count()} item(ns).",
                        request,
                    )

                messages.success(request, f"Locacao {locacao.codigo} cadastrada com sucesso.")
                return redirect("locacao_detail", pk=locacao.pk)
    else:
        form = LocacaoForm()
        item_formset = ItemLocacaoFormSet(prefix="itens", form_kwargs={"require_item": False})

    return render(
        request,
        "locacoes/form.html",
        with_layout(
            {
                "page_title": "Nova locacao",
                "form_title": "Nova locacao",
                "form_subtitle": "Cadastre os dados principais e informe os equipamentos da locacao.",
                "submit_label": "Salvar locacao",
                "form": form,
                "item_formset": item_formset,
            }
        ),
    )


def locacao_update(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if locacao.status not in [Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA]:
        messages.error(request, "Nao e possivel editar dados principais nesta etapa da locacao.")
        return redirect("locacao_detail", pk=locacao.pk)

    if request.method == "POST":
        form = LocacaoForm(request.POST, instance=locacao)
        if form.is_valid():
            conflitos = []
            if form.cleaned_data["status"] == Locacao.Status.AGENDADA:
                conflitos = _conflitos_reserva_ativos(
                    locacao.itens.values_list("ativo_id", flat=True),
                    form.cleaned_data["data_inicio"],
                    form.cleaned_data["data_fim"],
                    exclude_locacao_id=locacao.pk,
                )

            if conflitos:
                form.add_error(None, _mensagem_conflitos_reserva(conflitos))
            else:
                locacao = form.save()
                _registrar_historico(
                    locacao,
                    HistoricoLocacao.Tipo.EDICAO,
                    "Dados principais da locacao atualizados.",
                    request,
                )
                messages.success(request, f"Locacao {locacao.codigo} atualizada com sucesso.")
                return redirect("locacao_detail", pk=locacao.pk)
    else:
        form = LocacaoForm(instance=locacao)

    return render(
        request,
        "locacoes/form.html",
        with_layout(
            {
                "page_title": f"Editar {locacao.codigo}",
                "form_title": f"Editar locacao {locacao.codigo}",
                "form_subtitle": "Atualize os dados principais antes da ativacao da locacao.",
                "submit_label": "Salvar alteracoes",
                "form": form,
                "endereco_create_url": (
                    f'{reverse("cliente_endereco_create", kwargs={"pk": locacao.cliente.pk})}?locacao={locacao.pk}'
                ),
            }
        ),
    )


def locacao_detail(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente"), pk=pk)
    itens = list(locacao.itens.select_related("ativo", "ativo__categoria", "ativo__rastreador").order_by("ativo__codigo"))
    can_edit_itens = locacao.status in [Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA]
    historicos = locacao.historicos.order_by("-criado_em", "-id")[:10]

    if request.method == "POST":
        if not can_edit_itens:
            messages.error(request, "Nao e possivel alterar itens nesta etapa da locacao.")
            return redirect("locacao_detail", pk=locacao.pk)

        form = ItemLocacaoForm(request.POST, locacao=locacao)
        if form.is_valid():
            conflitos = []
            if locacao.status == Locacao.Status.AGENDADA:
                conflitos = _conflitos_reserva_ativos(
                    [form.cleaned_data["ativo"]],
                    locacao.data_inicio,
                    locacao.data_fim,
                    exclude_locacao_id=locacao.pk,
                )

            if conflitos:
                form.add_error("ativo", _mensagem_conflitos_reserva(conflitos))
            else:
                with transaction.atomic():
                    ativo = Ativo.objects.select_for_update().get(pk=form.cleaned_data["ativo"].pk)

                    if ativo.status != Ativo.Status.DISPONIVEL:
                        messages.error(request, "Este ativo nao esta disponivel para locacao.")
                        return redirect("locacao_detail", pk=locacao.pk)

                    item = form.save(commit=False)
                    item.locacao = locacao
                    item.ativo = ativo
                    item.save()
                    locacao.recalcular_totais()
                    locacao.sincronizar_status_ativos()
                    _registrar_historico(
                        locacao,
                        HistoricoLocacao.Tipo.ITEM_ADICIONADO,
                        f"Ativo {item.ativo.codigo} adicionado a locacao.",
                        request,
                    )

                messages.success(request, f"Ativo {item.ativo.codigo} adicionado a locacao.")
                return redirect("locacao_detail", pk=locacao.pk)
    else:
        form = ItemLocacaoForm(locacao=locacao)

    return render(
        request,
        "locacoes/detail.html",
        with_layout(
            {
                "page_title": locacao.codigo,
                "locacao": locacao,
                "itens": itens,
                "form": form,
                "can_edit_itens": can_edit_itens,
                "rastreamento_status": _rastreamento_status(itens),
                "historicos": historicos,
            }
        ),
    )


def locacao_item_remove(request, pk, item_pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("locacao_detail", pk=locacao.pk)

    if locacao.status not in [Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA]:
        messages.error(request, "Nao e possivel remover itens nesta etapa da locacao.")
        return redirect("locacao_detail", pk=locacao.pk)

    item = get_object_or_404(ItemLocacao, pk=item_pk, locacao=locacao)
    codigo_ativo = item.ativo.codigo
    item.delete()
    locacao.recalcular_totais()
    _registrar_historico(
        locacao,
        HistoricoLocacao.Tipo.ITEM_REMOVIDO,
        f"Ativo {codigo_ativo} removido da locacao.",
        request,
    )
    messages.success(request, f"Ativo {codigo_ativo} removido da locacao.")
    return redirect("locacao_detail", pk=locacao.pk)


def orcamento_aprovar(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("orcamentos")

    if locacao.status != Locacao.Status.ORCAMENTO:
        messages.error(request, "Somente orcamentos podem ser aprovados.")
        return redirect("locacao_detail", pk=locacao.pk)

    if not locacao.itens.exists():
        messages.error(request, "Adicione pelo menos um equipamento antes de aprovar o orcamento.")
        return redirect("locacao_detail", pk=locacao.pk)

    conflitos = _conflitos_reserva_locacao(locacao)
    if conflitos:
        messages.error(request, _mensagem_conflitos_reserva(conflitos))
        return redirect("locacao_detail", pk=locacao.pk)

    locacao.status = Locacao.Status.AGENDADA
    locacao.save(update_fields=["status", "atualizado_em"])
    _registrar_historico(
        locacao,
        HistoricoLocacao.Tipo.APROVACAO,
        "Orcamento aprovado e locacao agendada.",
        request,
    )
    messages.success(request, f"Orcamento {locacao.codigo} aprovado com sucesso.")
    return redirect("locacao_detail", pk=locacao.pk)


def orcamento_pdf(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente", "endereco_entrega"), pk=pk)

    if locacao.status != Locacao.Status.ORCAMENTO:
        messages.error(request, "PDF de orcamento disponivel apenas para locacoes em orcamento.")
        return redirect("locacao_detail", pk=locacao.pk)

    data_emissao = timezone.localdate()
    filename = f"orcamento-{locacao.codigo}.pdf"
    return PDFTemplateResponse(
        request=request,
        template="orcamentos/pdf.html",
        context={
            "locacao": locacao,
            "itens": _itens_locacao(locacao),
            "empresa": empresa_atual(),
            "data_emissao": data_emissao,
            "data_validade": data_emissao + timedelta(days=10),
            "periodo_dias": _periodo_dias(locacao),
        },
        filename=filename,
        show_content_in_browser=True,
        cmd_options=PDF_OPTIONS,
    )


def locacao_cancelar(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("locacao_detail", pk=locacao.pk)

    if locacao.status not in [Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA]:
        messages.error(request, "Somente orcamentos ou locacoes agendadas podem ser cancelados.")
        return redirect("locacao_detail", pk=locacao.pk)

    locacao.status = Locacao.Status.CANCELADA
    locacao.save(update_fields=["status", "atualizado_em"])
    locacao.cancelar_pagamento()
    _registrar_historico(
        locacao,
        HistoricoLocacao.Tipo.CANCELAMENTO,
        "Locacao cancelada.",
        request,
    )
    messages.success(request, f"Locacao {locacao.codigo} cancelada com sucesso.")
    return redirect("locacao_detail", pk=locacao.pk)


def locacao_ativar(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("locacao_detail", pk=locacao.pk)

    if not locacao.itens.exists():
        messages.error(request, "Adicione pelo menos um equipamento antes de ativar a locacao.")
        return redirect("locacao_detail", pk=locacao.pk)

    if locacao.status in [Locacao.Status.ATIVA, Locacao.Status.FINALIZADA, Locacao.Status.CANCELADA]:
        messages.error(request, "Esta locacao nao pode ser ativada neste status.")
        return redirect("locacao_detail", pk=locacao.pk)

    with transaction.atomic():
        locacao = get_object_or_404(Locacao.objects.select_for_update(), pk=pk)
        ativo_ids = locacao.itens.values_list("ativo_id", flat=True)
        ativos_indisponiveis = Ativo.objects.select_for_update().filter(pk__in=ativo_ids).exclude(
            status=Ativo.Status.DISPONIVEL
        )

        if ativos_indisponiveis.exists():
            codigos = ", ".join(ativos_indisponiveis.values_list("codigo", flat=True))
            messages.error(request, f"Nao foi possivel ativar. Equipamentos indisponiveis: {codigos}.")
            return redirect("locacao_detail", pk=locacao.pk)

        conflitos = _conflitos_reserva_locacao(locacao)
        if conflitos:
            messages.error(request, _mensagem_conflitos_reserva(conflitos))
            return redirect("locacao_detail", pk=locacao.pk)

        locacao.status = Locacao.Status.ATIVA
        locacao.save(update_fields=["status", "atualizado_em"])
        locacao.recalcular_totais()
        locacao.sincronizar_status_ativos()
        _registrar_historico(
            locacao,
            HistoricoLocacao.Tipo.ATIVACAO,
            "Locacao ativada e equipamentos sincronizados.",
            request,
        )

    messages.success(request, f"Locacao {locacao.codigo} ativada com sucesso.")
    return redirect("locacao_detail", pk=locacao.pk)


def termo_entrega_pdf(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente", "endereco_entrega"), pk=pk)

    if locacao.status != Locacao.Status.ATIVA:
        messages.error(request, "Termo de entrega disponivel apenas para locacoes ativas.")
        return redirect("locacao_detail", pk=locacao.pk)

    filename = f"termo-entrega-{locacao.codigo}.pdf"
    return PDFTemplateResponse(
        request=request,
        template="locacoes/termo_entrega_pdf.html",
        context={
            "locacao": locacao,
            "itens": _itens_locacao(locacao),
            "empresa": empresa_atual(),
            "data_entrega": timezone.localtime(),
        },
        filename=filename,
        show_content_in_browser=True,
        cmd_options=PDF_OPTIONS,
    )


def termo_devolucao_pdf(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente", "endereco_entrega"), pk=pk)

    if locacao.status not in [Locacao.Status.ATIVA, Locacao.Status.FINALIZADA]:
        messages.error(request, "Termo de devolucao disponivel apenas para locacoes ativas ou finalizadas.")
        return redirect("locacao_detail", pk=locacao.pk)

    filename = f"termo-devolucao-{locacao.codigo}.pdf"
    return PDFTemplateResponse(
        request=request,
        template="locacoes/termo_devolucao_pdf.html",
        context={
            "locacao": locacao,
            "itens": _itens_locacao(locacao),
            "empresa": empresa_atual(),
            "data_devolucao": timezone.localtime(),
        },
        filename=filename,
        show_content_in_browser=True,
        cmd_options=PDF_OPTIONS,
    )


def _itens_locacao(locacao):
    return locacao.itens.select_related("ativo", "ativo__categoria").order_by("ativo__codigo")


def _periodo_dias(locacao):
    return max((locacao.data_fim - locacao.data_inicio).days + 1, 1)


def _rastreamento_status(itens):
    rastreaveis = [item for item in itens if item.ativo.permite_rastreamento]

    return {
        "total": len(rastreaveis),
        "online": sum(1 for item in rastreaveis if getattr(item.ativo, "rastreador", None)),
    }


def _ativos_do_formset(item_formset):
    return [form.cleaned_data["ativo"] for form in item_formset if form.cleaned_data and form.cleaned_data.get("ativo")]


def _conflitos_reserva_locacao(locacao):
    return _conflitos_reserva_ativos(
        locacao.itens.values_list("ativo_id", flat=True),
        locacao.data_inicio,
        locacao.data_fim,
        exclude_locacao_id=locacao.pk,
    )


def _conflitos_reserva_ativos(ativos, data_inicio, data_fim, exclude_locacao_id=None):
    ativo_ids = [getattr(ativo, "pk", ativo) for ativo in ativos if ativo]

    if not ativo_ids or not data_inicio or not data_fim:
        return []

    conflitos = ItemLocacao.objects.select_related("ativo", "locacao", "locacao__cliente").filter(
        ativo_id__in=ativo_ids,
        locacao__status__in=[Locacao.Status.AGENDADA, Locacao.Status.ATIVA],
        locacao__data_inicio__lte=data_fim,
        locacao__data_fim__gte=data_inicio,
    )

    if exclude_locacao_id:
        conflitos = conflitos.exclude(locacao_id=exclude_locacao_id)

    return list(conflitos.order_by("ativo__codigo", "locacao__data_inicio", "locacao__codigo"))


def _mensagem_conflitos_reserva(conflitos):
    detalhes = []

    for conflito in conflitos[:4]:
        detalhes.append(
            (
                f"{conflito.ativo.codigo} reservado em {conflito.locacao.codigo} "
                f"({conflito.locacao.data_inicio:%d/%m/%Y} - {conflito.locacao.data_fim:%d/%m/%Y})"
            )
        )

    if len(conflitos) > 4:
        detalhes.append(f"mais {len(conflitos) - 4} conflito(s)")

    return f"Equipamento indisponivel no periodo: {'; '.join(detalhes)}."


def _registrar_historico(locacao, tipo, descricao, request):
    usuario_nome = ""

    if request.user.is_authenticated:
        usuario_nome = request.user.get_full_name() or request.user.get_username()

    return HistoricoLocacao.objects.create(
        locacao=locacao,
        tipo=tipo,
        descricao=descricao,
        usuario_nome=usuario_nome,
    )


def locacao_finalizar(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente"), pk=pk)
    itens = list(locacao.itens.select_related("ativo", "ativo__categoria", "ativo__rastreador").order_by("ativo__codigo"))

    if locacao.status != Locacao.Status.ATIVA:
        messages.error(request, "Somente locacoes ativas podem ser finalizadas.")
        return redirect("locacao_detail", pk=locacao.pk)

    if request.method == "POST":
        form = DevolucaoLocacaoForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                locacao = get_object_or_404(Locacao.objects.select_for_update(), pk=pk)
                locacao.status = Locacao.Status.FINALIZADA
                update_fields = ["status", "atualizado_em"]

                observacoes = form.cleaned_data["observacoes_devolucao"].strip()
                if observacoes:
                    locacao.observacoes = f"{locacao.observacoes}\n\nDevolucao: {observacoes}".strip()
                    update_fields.append("observacoes")

                locacao.save(update_fields=update_fields)
                locacao.finalizar_operacao()
                _registrar_historico(
                    locacao,
                    HistoricoLocacao.Tipo.FINALIZACAO,
                    "Locacao finalizada e equipamentos liberados.",
                    request,
                )

            messages.success(request, f"Locacao {locacao.codigo} finalizada com sucesso.")
            return redirect("locacao_detail", pk=locacao.pk)
    else:
        form = DevolucaoLocacaoForm()

    return render(
        request,
        "locacoes/finalizacao_form.html",
        with_layout(
            {
                "page_title": f"Finalizar {locacao.codigo}",
                "locacao": locacao,
                "itens": itens,
                "form": form,
            }
        ),
    )
