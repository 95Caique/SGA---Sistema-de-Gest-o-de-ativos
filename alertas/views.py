from datetime import timedelta

from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from config.views import with_layout
from locacoes.models import Locacao
from manutencao.models import OrdemManutencao
from rastreamento.models import Rastreador


def alertas_list(request):
    query = request.GET.get("q", "").strip()
    tipo_filter = request.GET.get("tipo", "").strip()
    tipos_validos = ["rastreamento", "manutencao", "locacao"]

    alertas = _alertas_rastreamento() + _alertas_manutencao() + _alertas_locacao()

    if tipo_filter in tipos_validos:
        alertas = [alerta for alerta in alertas if alerta["tipo"] == tipo_filter]
    else:
        tipo_filter = ""

    if query:
        termo = query.lower()
        alertas = [
            alerta
            for alerta in alertas
            if termo in alerta["origem"].lower() or termo in alerta["mensagem"].lower() or termo in alerta["referencia"].lower()
        ]

    prioridade_ordem = {"alta": 0, "media": 1, "baixa": 2}
    alertas.sort(key=lambda alerta: (prioridade_ordem[alerta["prioridade"]], alerta["origem"]))

    return render(
        request,
        "alertas/list.html",
        with_layout(
            {
                "page_title": "Alertas",
                "alertas": alertas,
                "query": query,
                "tipo_filter": tipo_filter,
                "status_counts": {
                    "todos": len(alertas),
                    "altas": sum(1 for alerta in alertas if alerta["prioridade"] == "alta"),
                    "medias": sum(1 for alerta in alertas if alerta["prioridade"] == "media"),
                    "baixas": sum(1 for alerta in alertas if alerta["prioridade"] == "baixa"),
                },
            }
        ),
    )


def _alertas_rastreamento():
    rastreadores = Rastreador.objects.select_related("ativo").filter(status=Rastreador.Status.SEM_COMUNICACAO)
    return [
        {
            "tipo": "rastreamento",
            "tipo_label": "Rastreamento",
            "origem": rastreador.ativo.codigo,
            "referencia": rastreador.ativo.nome,
            "mensagem": "Rastreador sem comunicacao.",
            "prioridade": "alta",
            "prioridade_label": "Alta",
            "link": reverse("rastreamento"),
        }
        for rastreador in rastreadores
    ]


def _alertas_manutencao():
    ordens = OrdemManutencao.objects.select_related("ativo").filter(
        prioridade=OrdemManutencao.Prioridade.ALTA,
        status__in=[OrdemManutencao.Status.ABERTA, OrdemManutencao.Status.EM_ANDAMENTO],
    )
    return [
        {
            "tipo": "manutencao",
            "tipo_label": "Manutencao",
            "origem": ordem.codigo,
            "referencia": ordem.ativo.codigo,
            "mensagem": "Manutencao de alta prioridade em aberto.",
            "prioridade": "alta",
            "prioridade_label": "Alta",
            "link": reverse("manutencao"),
        }
        for ordem in ordens
    ]


def _alertas_locacao():
    hoje = timezone.localdate()
    limite = hoje + timedelta(days=2)
    locacoes = Locacao.objects.select_related("cliente").filter(
        Q(status=Locacao.Status.ATIVA) | Q(status=Locacao.Status.AGENDADA),
        data_fim__range=(hoje, limite),
    )
    return [
        {
            "tipo": "locacao",
            "tipo_label": "Locacao",
            "origem": locacao.codigo,
            "referencia": locacao.cliente.nome,
            "mensagem": f"Devolucao prevista para {locacao.data_fim:%d/%m/%Y}.",
            "prioridade": "media",
            "prioridade_label": "Media",
            "link": reverse("locacao_detail", kwargs={"pk": locacao.pk}),
        }
        for locacao in locacoes
    ]
