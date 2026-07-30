from decimal import Decimal

from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from config.views import money_br, with_layout
from locacoes.models import Locacao


STATUS_PAGAMENTO_VALIDOS = [status for status, _label in Locacao.StatusPagamento.choices]


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

    if status_filter in STATUS_PAGAMENTO_VALIDOS:
        locacoes = locacoes.filter(status_pagamento=status_filter)
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


def financeiro_receber(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("financeiro")

    if locacao.status_pagamento == Locacao.StatusPagamento.CANCELADO:
        messages.error(request, "Nao e possivel receber uma locacao cancelada.")
        return redirect("financeiro")

    locacao.marcar_recebida(timezone.localdate())
    messages.success(request, f"Pagamento da locacao {locacao.codigo} marcado como recebido.")
    return redirect("financeiro")


def financeiro_reabrir(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method != "POST":
        return redirect("financeiro")

    if locacao.status_pagamento != Locacao.StatusPagamento.RECEBIDO:
        messages.error(request, "Somente pagamentos recebidos podem ser reabertos.")
        return redirect("financeiro")

    locacao.reabrir_pagamento()
    messages.success(request, f"Pagamento da locacao {locacao.codigo} reaberto.")
    return redirect("financeiro")


def _total_por_status_pagamento(status_pagamento):
    return _locacoes_por_pagamento(status_pagamento).aggregate(total=Sum("valor_total"))["total"] or Decimal("0")


def _locacoes_por_pagamento(status_pagamento):
    return Locacao.objects.filter(status_pagamento=status_pagamento)


def _resumo_status(status_pagamento, valor):
    locacoes = _locacoes_por_pagamento(status_pagamento)

    return {
        "valor": money_br(valor),
        "count": locacoes.count(),
    }


def _resumo_financeiro():
    aberto = _total_por_status_pagamento(Locacao.StatusPagamento.ABERTO)
    recebido = _total_por_status_pagamento(Locacao.StatusPagamento.RECEBIDO)
    cancelado = _total_por_status_pagamento(Locacao.StatusPagamento.CANCELADO)

    return {
        "aberto": _resumo_status(Locacao.StatusPagamento.ABERTO, aberto),
        "recebido": _resumo_status(Locacao.StatusPagamento.RECEBIDO, recebido),
        "cancelado": _resumo_status(Locacao.StatusPagamento.CANCELADO, cancelado),
        "total": money_br(aberto + recebido),
    }
