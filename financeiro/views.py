from decimal import Decimal

from django.db.models import Q, Sum
from django.shortcuts import render

from config.views import money_br, with_layout
from locacoes.models import Locacao


STATUS_ABERTOS = [Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA, Locacao.Status.ATIVA]


def financeiro_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    locacoes = Locacao.objects.select_related("cliente").order_by("data_fim", "codigo")

    if query:
        locacoes = locacoes.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    if status_filter == "aberto":
        locacoes = locacoes.filter(status__in=STATUS_ABERTOS)
    elif status_filter == "recebido":
        locacoes = locacoes.filter(status=Locacao.Status.FINALIZADA)
    elif status_filter == "cancelado":
        locacoes = locacoes.filter(status=Locacao.Status.CANCELADA)
    else:
        status_filter = ""

    resumo = _resumo_financeiro()

    return render(
        request,
        "financeiro/list.html",
        with_layout(
            {
                "page_title": "Financeiro",
                "locacoes": locacoes,
                "query": query,
                "status_filter": status_filter,
                "resumo": resumo,
            }
        ),
    )


def _total_por_status(status):
    return Locacao.objects.filter(status__in=status).aggregate(total=Sum("valor_total"))["total"] or Decimal("0")


def _resumo_financeiro():
    aberto = _total_por_status(STATUS_ABERTOS)
    recebido = _total_por_status([Locacao.Status.FINALIZADA])
    cancelado = _total_por_status([Locacao.Status.CANCELADA])

    return {
        "aberto": {"valor": money_br(aberto), "count": Locacao.objects.filter(status__in=STATUS_ABERTOS).count()},
        "recebido": {"valor": money_br(recebido), "count": Locacao.objects.filter(status=Locacao.Status.FINALIZADA).count()},
        "cancelado": {"valor": money_br(cancelado), "count": Locacao.objects.filter(status=Locacao.Status.CANCELADA).count()},
        "total": money_br(aberto + recebido),
    }
