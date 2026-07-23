from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from config.views import money_br, with_layout
from locacoes.models import Locacao


STATUS_FILTROS = ["minuta", "ativo", "vencido", "encerrado", "cancelado"]


def contratos_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    locacoes = Locacao.objects.select_related("cliente").annotate(total_itens=Count("itens")).order_by("-data_inicio")

    if query:
        locacoes = locacoes.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    contratos = [_contrato_from_locacao(locacao) for locacao in locacoes]

    if status_filter in STATUS_FILTROS:
        contratos = [contrato for contrato in contratos if contrato["status_key"] == status_filter]
    else:
        status_filter = ""

    return render(
        request,
        "contratos/list.html",
        with_layout(
            {
                "page_title": "Contratos",
                "contratos": contratos,
                "query": query,
                "status_filter": status_filter,
                "status_counts": _status_counts(),
            }
        ),
    )


def _contrato_from_locacao(locacao):
    status_key, status_label = _status_contrato(locacao)
    return {
        "codigo": f"CTR-{locacao.codigo}",
        "locacao": locacao,
        "cliente": locacao.cliente,
        "inicio": locacao.data_inicio,
        "fim": locacao.data_fim,
        "total_itens": locacao.total_itens,
        "valor_total": money_br(locacao.valor_total),
        "status_key": status_key,
        "status_label": status_label,
    }


def _status_contrato(locacao):
    hoje = timezone.localdate()

    if locacao.status == Locacao.Status.ORCAMENTO:
        return "minuta", "Minuta"
    if locacao.status == Locacao.Status.FINALIZADA:
        return "encerrado", "Encerrado"
    if locacao.status == Locacao.Status.CANCELADA:
        return "cancelado", "Cancelado"
    if locacao.status == Locacao.Status.ATIVA and locacao.data_fim < hoje:
        return "vencido", "Vencido"
    return "ativo", "Ativo"


def _status_counts():
    contratos = [_contrato_from_locacao(locacao) for locacao in Locacao.objects.select_related("cliente").annotate(total_itens=Count("itens"))]
    return {
        "todos": len(contratos),
        "minutas": sum(1 for contrato in contratos if contrato["status_key"] == "minuta"),
        "ativos": sum(1 for contrato in contratos if contrato["status_key"] == "ativo"),
        "vencidos": sum(1 for contrato in contratos if contrato["status_key"] == "vencido"),
        "encerrados": sum(1 for contrato in contratos if contrato["status_key"] == "encerrado"),
        "cancelados": sum(1 for contrato in contratos if contrato["status_key"] == "cancelado"),
    }

# Create your views here.
