from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import render

from config.views import with_layout
from locacoes.models import ItemLocacao, Locacao

from .models import PosicaoRastreamento, Rastreador


def rastreamento_mapa(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_validos = [status for status, _label in Rastreador.Status.choices]
    ultima_posicao = PosicaoRastreamento.objects.filter(rastreador=OuterRef("pk")).order_by("-registrada_em")
    rastreadores = Rastreador.objects.select_related("ativo").annotate(
        ultima_latitude=Subquery(ultima_posicao.values("latitude")[:1]),
        ultima_longitude=Subquery(ultima_posicao.values("longitude")[:1]),
        ultimo_endereco=Subquery(ultima_posicao.values("endereco_referencia")[:1]),
        ultima_velocidade=Subquery(ultima_posicao.values("velocidade_kmh")[:1]),
        ultima_data=Subquery(ultima_posicao.values("registrada_em")[:1]),
    )

    if query:
        rastreadores = rastreadores.filter(
            Q(identificador__icontains=query)
            | Q(ativo__codigo__icontains=query)
            | Q(ativo__nome__icontains=query)
            | Q(ativo__localizacao_atual__icontains=query)
        )

    if status_filter in status_validos:
        rastreadores = rastreadores.filter(status=status_filter)

    rastreadores = list(rastreadores)
    locacoes_ativas = _locacoes_ativas_por_ativo([rastreador.ativo_id for rastreador in rastreadores])

    for rastreador in rastreadores:
        rastreador.locacao_ativa = locacoes_ativas.get(rastreador.ativo_id)

    status_counts = {
        "rastreados": Rastreador.objects.count(),
        "online": Rastreador.objects.filter(status=Rastreador.Status.ONLINE).count(),
        "parados": Rastreador.objects.filter(status=Rastreador.Status.OFFLINE).count(),
        "sem_comunicacao": Rastreador.objects.filter(status=Rastreador.Status.SEM_COMUNICACAO).count(),
    }

    return render(
        request,
        "rastreamento/mapa.html",
        with_layout(
            {
                "page_title": "Rastreamento",
                "query": query,
                "status_filter": status_filter if status_filter in status_validos else "",
                "status_options": Rastreador.Status.choices,
                "rastreadores": rastreadores,
                "map_points": _map_points(rastreadores),
                "itens_sem_rastreamento": _itens_sem_rastreamento(),
                "status_counts": status_counts,
            }
        ),
    )


def _locacoes_ativas_por_ativo(ativo_ids):
    locacoes = (
        Locacao.objects.select_related("cliente")
        .filter(status=Locacao.Status.ATIVA, itens__ativo_id__in=ativo_ids)
        .distinct()
        .order_by("-data_inicio", "codigo")
    )

    locacoes_por_ativo = {}
    for locacao in locacoes.prefetch_related("itens"):
        for item in locacao.itens.all():
            if item.ativo_id in ativo_ids and item.ativo_id not in locacoes_por_ativo:
                locacoes_por_ativo[item.ativo_id] = locacao

    return locacoes_por_ativo


def _itens_sem_rastreamento():
    return (
        ItemLocacao.objects.select_related("ativo", "locacao", "locacao__cliente")
        .filter(locacao__status=Locacao.Status.ATIVA)
        .filter(Q(ativo__permite_rastreamento=False) | Q(ativo__rastreador__isnull=True))
        .order_by("locacao__codigo", "ativo__codigo")[:6]
    )


def _map_points(rastreadores):
    points = []

    for rastreador in rastreadores:
        if rastreador.ultima_latitude is None or rastreador.ultima_longitude is None:
            continue

        points.append(
            {
                "id": rastreador.pk,
                "name": rastreador.ativo.nome,
                "code": rastreador.ativo.codigo,
                "status": rastreador.status,
                "statusLabel": rastreador.get_status_display(),
                "lat": float(rastreador.ultima_latitude),
                "lng": float(rastreador.ultima_longitude),
                "speed": float(rastreador.ultima_velocidade or 0),
                "battery": rastreador.bateria_percentual,
                "signal": rastreador.sinal_gsm_percentual,
                "address": rastreador.ultimo_endereco or rastreador.ativo.localizacao_atual or "Sem posicao registrada",
                "rental": rastreador.locacao_ativa.codigo if rastreador.locacao_ativa else "",
                "client": rastreador.locacao_ativa.cliente.nome if rastreador.locacao_ativa else "",
            }
        )

    return points
