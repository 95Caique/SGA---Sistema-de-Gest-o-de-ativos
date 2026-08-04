from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from config.views import money_br, with_layout

from .forms import ConclusaoManutencaoForm, OrdemManutencaoForm
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

    for ordem in ordens:
        ordem.custo_estimado_display = money_br(ordem.custo_estimado)
        ordem.custo_real_display = money_br(ordem.custo_real)

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
            return redirect("manutencao_detail", pk=ordem.pk)
    else:
        form = OrdemManutencaoForm()

    return render(
        request,
        "manutencao/form.html",
        with_layout(
            {
                "page_title": "Nova manutencao",
                "form": form,
                "ativos_detalhes": _ativos_detalhes(form.fields["ativo"].queryset),
            }
        ),
    )


def manutencao_detail(request, pk):
    ordem = get_object_or_404(OrdemManutencao.objects.select_related("ativo", "ativo__categoria"), pk=pk)
    can_start = ordem.status == OrdemManutencao.Status.ABERTA
    can_close = ordem.status not in [OrdemManutencao.Status.FINALIZADA, OrdemManutencao.Status.CANCELADA]

    return render(
        request,
        "manutencao/detail.html",
        with_layout(
            {
                "page_title": ordem.codigo,
                "ordem": ordem,
                "can_start": can_start,
                "can_close": can_close,
                "custo_estimado_display": money_br(ordem.custo_estimado),
                "custo_real_display": money_br(ordem.custo_real),
            }
        ),
    )


def manutencao_iniciar(request, pk):
    ordem = get_object_or_404(OrdemManutencao, pk=pk)

    if request.method != "POST":
        return redirect("manutencao_detail", pk=ordem.pk)

    if ordem.status != OrdemManutencao.Status.ABERTA:
        messages.error(request, "Somente ordens abertas podem ser iniciadas.")
        return redirect("manutencao_detail", pk=ordem.pk)

    ordem.iniciar()
    messages.success(request, f"Ordem {ordem.codigo} iniciada com sucesso.")
    return redirect("manutencao_detail", pk=ordem.pk)


def manutencao_finalizar(request, pk):
    ordem = get_object_or_404(OrdemManutencao, pk=pk)

    if ordem.status in [OrdemManutencao.Status.FINALIZADA, OrdemManutencao.Status.CANCELADA]:
        messages.error(request, "Esta ordem nao pode ser finalizada.")
        return redirect("manutencao_detail", pk=ordem.pk)

    if request.method == "POST":
        form = ConclusaoManutencaoForm(request.POST, instance=ordem)
        if form.is_valid():
            ordem.finalizar(
                solucao=form.cleaned_data["solucao"],
                custo_real=form.cleaned_data["custo_real"],
            )
            messages.success(request, f"Ordem {ordem.codigo} finalizada com sucesso.")
            return redirect("manutencao_detail", pk=ordem.pk)
    else:
        form = ConclusaoManutencaoForm(instance=ordem)

    return render(
        request,
        "manutencao/conclusao_form.html",
        with_layout(
            {
                "page_title": f"Finalizar {ordem.codigo}",
                "ordem": ordem,
                "form": form,
            }
        ),
    )


def manutencao_cancelar(request, pk):
    ordem = get_object_or_404(OrdemManutencao, pk=pk)

    if request.method != "POST":
        return redirect("manutencao_detail", pk=ordem.pk)

    if ordem.status in [OrdemManutencao.Status.FINALIZADA, OrdemManutencao.Status.CANCELADA]:
        messages.error(request, "Esta ordem nao pode ser cancelada.")
        return redirect("manutencao_detail", pk=ordem.pk)

    ordem.cancelar()
    messages.success(request, f"Ordem {ordem.codigo} cancelada com sucesso.")
    return redirect("manutencao_detail", pk=ordem.pk)


def _ativos_detalhes(ativos):
    return [
        {
            "id": ativo.pk,
            "codigo": ativo.codigo,
            "nome": ativo.nome,
            "categoria": ativo.categoria.nome,
            "status": ativo.get_status_display(),
            "localizacao": ativo.localizacao_atual or "Deposito",
            "horimetro": ativo.horimetro_atual,
            "proxima_manutencao": ativo.proxima_manutencao_horas,
            "rastreamento": "Sim" if ativo.permite_rastreamento else "Nao",
        }
        for ativo in ativos.select_related("categoria")
    ]
