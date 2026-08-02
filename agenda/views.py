from datetime import timedelta

from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from config.views import with_layout
from locacoes.models import Locacao


def _evento_agenda(locacao, tipo, hoje):
    data = locacao.data_inicio if tipo == "entrega" else locacao.data_fim
    situacao = _situacao_evento(data, hoje)

    return {
        "data": data,
        "tipo": tipo,
        "tipo_label": "Entrega" if tipo == "entrega" else "Devolucao",
        "situacao": situacao["key"],
        "situacao_label": situacao["label"],
        "locacao": locacao,
        "status": locacao.get_status_display(),
        "status_key": locacao.status,
        "total_itens": locacao.total_itens,
    }


def agenda_list(request):
    query = request.GET.get("q", "").strip()
    tipo_filter = request.GET.get("tipo", "").strip()
    situacao_filter = request.GET.get("situacao", "").strip()
    tipos_validos = ["entrega", "devolucao"]
    situacoes_validas = ["atrasado", "hoje", "proximo", "futuro"]
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

    hoje = timezone.localdate()
    eventos = _eventos_locacoes(locacoes, hoje)
    status_counts = _status_counts(eventos)

    if tipo_filter in tipos_validos:
        eventos = [evento for evento in eventos if evento["tipo"] == tipo_filter]
    else:
        tipo_filter = ""

    if situacao_filter in situacoes_validas:
        eventos = [evento for evento in eventos if evento["situacao"] == situacao_filter]
    else:
        situacao_filter = ""

    eventos.sort(key=lambda evento: (evento["data"], evento["locacao"].codigo, evento["tipo"]))

    return render(
        request,
        "agenda/list.html",
        with_layout(
            {
                "page_title": "Agenda",
                "eventos": eventos,
                "query": query,
                "tipo_filter": tipo_filter,
                "situacao_filter": situacao_filter,
                "situacao_options": [
                    ("atrasado", "Atrasados"),
                    ("hoje", "Hoje"),
                    ("proximo", "Proximos"),
                    ("futuro", "Futuros"),
                ],
                "status_counts": status_counts,
            }
        ),
    )


def _eventos_locacoes(locacoes, hoje):
    eventos = []

    for locacao in locacoes:
        eventos.append(_evento_agenda(locacao, "entrega", hoje))
        eventos.append(_evento_agenda(locacao, "devolucao", hoje))

    return eventos


def _situacao_evento(data, hoje):
    if data < hoje:
        return {"key": "atrasado", "label": "Atrasado"}

    if data == hoje:
        return {"key": "hoje", "label": "Hoje"}

    if data <= hoje + timedelta(days=2):
        return {"key": "proximo", "label": "Proximo"}

    return {"key": "futuro", "label": "Futuro"}


def _status_counts(eventos):
    return {
        "todos": len(eventos),
        "entregas": sum(1 for evento in eventos if evento["tipo"] == "entrega"),
        "devolucoes": sum(1 for evento in eventos if evento["tipo"] == "devolucao"),
        "atrasados": sum(1 for evento in eventos if evento["situacao"] == "atrasado"),
        "hoje": sum(1 for evento in eventos if evento["situacao"] == "hoje"),
        "proximos": sum(1 for evento in eventos if evento["situacao"] == "proximo"),
    }
