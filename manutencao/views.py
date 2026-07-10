from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from config.views import with_layout

from .forms import OrdemManutencaoForm
from .models import OrdemManutencao


def manutencoes_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_validos = [status for status, _label in OrdemManutencao.Status.choices]
    ordens = OrdemManutencao.objects.select_related("ativo", "ativo__categoria").order_by("status", "-data_abertura")

    if query:
        ordens = ordens.filter(
            Q(codigo__icontains=query)
            | Q(ativo__codigo__icontains=query)
            | Q(ativo__nome__icontains=query)
            | Q(responsavel__icontains=query)
            | Q(descricao__icontains=query)
        )

    if status_filter in status_validos:
        ordens = ordens.filter(status=status_filter)

    status_counts = {
        "todos": OrdemManutencao.objects.count(),
        "abertas": OrdemManutencao.objects.filter(status=OrdemManutencao.Status.ABERTA).count(),
        "andamento": OrdemManutencao.objects.filter(status=OrdemManutencao.Status.EM_ANDAMENTO).count(),
        "finalizadas": OrdemManutencao.objects.filter(status=OrdemManutencao.Status.FINALIZADA).count(),
        "canceladas": OrdemManutencao.objects.filter(status=OrdemManutencao.Status.CANCELADA).count(),
    }

    return render(
        request,
        "manutencao/list.html",
        with_layout(
            {
                "page_title": "Manutencao",
                "ordens": ordens,
                "query": query,
                "status_filter": status_filter if status_filter in status_validos else "",
                "status_counts": status_counts,
            }
        ),
    )


def manutencao_create(request):
    if request.method == "POST":
        form = OrdemManutencaoForm(request.POST)
        if form.is_valid():
            ordem = form.save()
            ordem.colocar_ativo_em_manutencao()
            messages.success(request, f"Ordem {ordem.codigo} aberta com sucesso.")
            return redirect("manutencao")
    else:
        form = OrdemManutencaoForm()

    return render(
        request,
        "manutencao/form.html",
        with_layout(
            {
                "page_title": "Nova manutencao",
                "form": form,
            }
        ),
    )


def manutencao_finalizar(request, pk):
    ordem = get_object_or_404(OrdemManutencao, pk=pk)

    if request.method != "POST":
        return redirect("manutencao")

    if ordem.status in [OrdemManutencao.Status.FINALIZADA, OrdemManutencao.Status.CANCELADA]:
        messages.error(request, "Esta ordem nao pode ser finalizada.")
        return redirect("manutencao")

    ordem.finalizar()
    messages.success(request, f"Ordem {ordem.codigo} finalizada com sucesso.")
    return redirect("manutencao")
