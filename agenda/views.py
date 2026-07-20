from django.db.models import Count, Q
from django.shortcuts import render

from config.views import with_layout
from locacoes.models import Locacao


def _evento_agenda(locacao, tipo):
    data = locacao.data_inicio if tipo == "entrega" else locacao.data_fim
    return {
        "data": data,
        "tipo": tipo,
        "tipo_label": "Entrega" if tipo == "entrega" else "Devolucao",
        "locacao": locacao,
        "status": locacao.get_status_display(),
        "status_key": locacao.status,
        "total_itens": locacao.total_itens,
    }


def agenda_list(request):
    query = request.GET.get("q", "").strip()
    tipo_filter = request.GET.get("tipo", "").strip()
    tipos_validos = ["entrega", "devolucao"]
    locacoes = (
        Locacao.objects.select_related("cliente")
        .annotate(total_itens=Count("itens"))
        .exclude(status=Locacao.Status.CANCELADA)
        .order_by("data_inicio", "codigo")
    )

    if query:
        locacoes = locacoes.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    eventos = []
    for locacao in locacoes:
        if tipo_filter in ["", "entrega"]:
            eventos.append(_evento_agenda(locacao, "entrega"))
        if tipo_filter in ["", "devolucao"]:
            eventos.append(_evento_agenda(locacao, "devolucao"))

    eventos.sort(key=lambda evento: (evento["data"], evento["locacao"].codigo, evento["tipo"]))
    status_counts = {
        "todos": locacoes.count() * 2,
        "entregas": locacoes.count(),
        "devolucoes": locacoes.count(),
    }

    return render(
        request,
        "agenda/list.html",
        with_layout(
            {
                "page_title": "Agenda",
                "eventos": eventos,
                "query": query,
                "tipo_filter": tipo_filter if tipo_filter in tipos_validos else "",
                "status_counts": status_counts,
            }
        ),
    )
