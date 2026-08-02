from decimal import Decimal

from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from config.views import money_br, with_layout
from locacoes.models import Locacao


STATUS_PAGAMENTO_VALIDOS = [status for status, _label in Locacao.StatusPagamento.choices]
SITUACOES_VALIDAS = ["vencido", "vence_hoje", "a_vencer", "quitado", "cancelado"]


def financeiro_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    situacao_filter = request.GET.get("situacao", "").strip()
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

    locacoes = list(locacoes)
    _preparar_lancamentos(locacoes)

    if situacao_filter in SITUACOES_VALIDAS:
        locacoes = [locacao for locacao in locacoes if locacao.situacao_financeira == situacao_filter]
    else:
        situacao_filter = ""

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
                "situacao_filter": situacao_filter,
                "situacao_options": [
                    ("vencido", "Vencidos"),
                    ("vence_hoje", "Vencem hoje"),
                    ("a_vencer", "A vencer"),
                    ("quitado", "Quitados"),
                    ("cancelado", "Cancelados"),
                ],
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
    locacoes_vencidas = _locacoes_vencidas()
    vencido = locacoes_vencidas.aggregate(total=Sum("valor_total"))["total"] or Decimal("0")

    return {
        "aberto": _resumo_status(Locacao.StatusPagamento.ABERTO, aberto),
        "recebido": _resumo_status(Locacao.StatusPagamento.RECEBIDO, recebido),
        "cancelado": _resumo_status(Locacao.StatusPagamento.CANCELADO, cancelado),
        "vencido": {
            "valor": money_br(vencido),
            "count": locacoes_vencidas.count(),
        },
        "total": money_br(aberto + recebido),
    }


def _locacoes_vencidas():
    return Locacao.objects.filter(
        status_pagamento=Locacao.StatusPagamento.ABERTO,
        data_fim__lt=timezone.localdate(),
    ).exclude(status=Locacao.Status.CANCELADA)


def _preparar_lancamentos(locacoes):
    for locacao in locacoes:
        situacao = _situacao_financeira(locacao)
        locacao.valor_total_display = money_br(locacao.valor_total)
        locacao.situacao_financeira = situacao["key"]
        locacao.situacao_financeira_label = situacao["label"]
        locacao.situacao_financeira_tone = situacao["tone"]


def _situacao_financeira(locacao):
    if locacao.status_pagamento == Locacao.StatusPagamento.CANCELADO:
        return {"key": "cancelado", "label": "Cancelado", "tone": "danger"}

    if locacao.status_pagamento == Locacao.StatusPagamento.RECEBIDO:
        return {"key": "quitado", "label": "Quitado", "tone": "success"}

    hoje = timezone.localdate()

    if locacao.data_fim < hoje:
        return {"key": "vencido", "label": "Vencido", "tone": "danger"}

    if locacao.data_fim == hoje:
        return {"key": "vence_hoje", "label": "Vence hoje", "tone": "warning"}

    return {"key": "a_vencer", "label": "A vencer", "tone": "neutral"}
