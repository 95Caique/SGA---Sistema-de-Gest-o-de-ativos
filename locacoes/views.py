from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from ativos.models import Ativo
from config.views import with_layout

from .forms import ItemLocacaoForm, LocacaoForm
from .models import ItemLocacao, Locacao


def locacoes_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_validos = [status for status, _label in Locacao.Status.choices]
    locacoes = Locacao.objects.select_related("cliente").annotate(total_itens=Count("itens")).order_by("-data_inicio")

    if query:
        locacoes = locacoes.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    if status_filter in status_validos:
        locacoes = locacoes.filter(status=status_filter)

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
            }
        ),
    )


def locacao_create(request):
    if request.method == "POST":
        form = LocacaoForm(request.POST)
        if form.is_valid():
            locacao = form.save()
            messages.success(request, f"Locacao {locacao.codigo} cadastrada com sucesso.")
            return redirect("locacao_detail", pk=locacao.pk)
    else:
        form = LocacaoForm()

    return render(
        request,
        "locacoes/form.html",
        with_layout(
            {
                "page_title": "Nova locacao",
                "form_title": "Nova locacao",
                "form_subtitle": "Cadastre os dados principais da locacao. Os equipamentos entram na proxima etapa.",
                "submit_label": "Salvar locacao",
                "form": form,
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
            locacao = form.save()
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
            }
        ),
    )


def locacao_detail(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente"), pk=pk)
    itens = locacao.itens.select_related("ativo", "ativo__categoria").order_by("ativo__codigo")
    can_edit_itens = locacao.status in [Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA]

    if request.method == "POST":
        if not can_edit_itens:
            messages.error(request, "Nao e possivel alterar itens nesta etapa da locacao.")
            return redirect("locacao_detail", pk=locacao.pk)

        form = ItemLocacaoForm(request.POST)
        if form.is_valid():
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

            messages.success(request, f"Ativo {item.ativo.codigo} adicionado a locacao.")
            return redirect("locacao_detail", pk=locacao.pk)
    else:
        form = ItemLocacaoForm()

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
    messages.success(request, f"Ativo {codigo_ativo} removido da locacao.")
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

        locacao.status = Locacao.Status.ATIVA
        locacao.save(update_fields=["status", "atualizado_em"])
        locacao.recalcular_totais()
        locacao.sincronizar_status_ativos()

    messages.success(request, f"Locacao {locacao.codigo} ativada com sucesso.")
    return redirect("locacao_detail", pk=locacao.pk)


def locacao_finalizar(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("locacao_detail", pk=locacao.pk)

    if locacao.status != Locacao.Status.ATIVA:
        messages.error(request, "Somente locacoes ativas podem ser finalizadas.")
        return redirect("locacao_detail", pk=locacao.pk)

    locacao.status = Locacao.Status.FINALIZADA
    locacao.save(update_fields=["status", "atualizado_em"])
    locacao.finalizar_operacao()
    messages.success(request, f"Locacao {locacao.codigo} finalizada com sucesso.")
    return redirect("locacao_detail", pk=locacao.pk)
