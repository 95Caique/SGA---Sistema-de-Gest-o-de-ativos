from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import render

from config.views import with_layout

from .models import PosicaoRastreamento, Rastreador


def rastreamento_mapa(request):
    query = request.GET.get("q", "").strip()
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
                "rastreadores": rastreadores,
                "status_counts": status_counts,
            }
        ),
    )
