from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from ativos.models import Ativo
from config.views import with_layout

from .forms import ItemLocacaoForm, LocacaoForm
from .models import Locacao


def locacoes_list(request):
    query = request.GET.get("q", "").strip()
    locacoes = Locacao.objects.select_related("cliente").annotate(total_itens=Count("itens")).order_by("-data_inicio")

    if query:
        locacoes = locacoes.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    status_counts = {
        "todos": Locacao.objects.count(),
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
                "form": form,
            }
        ),
    )


def locacao_detail(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente"), pk=pk)
    itens = locacao.itens.select_related("ativo", "ativo__categoria").order_by("ativo__codigo")

    if request.method == "POST":
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
            }
        ),
    )


def locacao_ativar(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("locacao_detail", pk=locacao.pk)

    if not locacao.itens.exists():
        messages.error(request, "Adicione pelo menos um equipamento antes de ativar a locacao.")
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
