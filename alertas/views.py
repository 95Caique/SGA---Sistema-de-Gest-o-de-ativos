from datetime import date, timedelta

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
    alertas.sort(key=lambda alerta: (prioridade_ordem[alerta["prioridade"]], alerta["prazo"] or date.max, alerta["origem"]))

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
            "prazo": rastreador.atualizado_em.date(),
            "prazo_label": "Ultima atualizacao",
            "prioridade": "alta",
            "prioridade_label": "Alta",
            "link": reverse("rastreamento"),
        }
        for rastreador in rastreadores
    ]


def _alertas_manutencao():
    hoje = timezone.localdate()
    ordens = OrdemManutencao.objects.select_related("ativo").filter(
        status__in=[OrdemManutencao.Status.ABERTA, OrdemManutencao.Status.EM_ANDAMENTO],
    )
    alertas = []

    for ordem in ordens:
        if ordem.data_prevista and ordem.data_prevista < hoje:
            alertas.append(_alerta_manutencao(ordem, "Manutencao vencida.", "alta", "Alta"))
            continue

        if ordem.prioridade == OrdemManutencao.Prioridade.ALTA:
            alertas.append(_alerta_manutencao(ordem, "Manutencao de alta prioridade em aberto.", "alta", "Alta"))

    return alertas


def _alertas_locacao():
    hoje = timezone.localdate()
    limite = hoje + timedelta(days=2)
    locacoes = Locacao.objects.select_related("cliente").filter(
        Q(status=Locacao.Status.ATIVA) | Q(status=Locacao.Status.AGENDADA),
        data_fim__lte=limite,
    )
    alertas = []

    for locacao in locacoes:
        if locacao.data_fim < hoje:
            alertas.append(_alerta_locacao(locacao, "Devolucao vencida.", "alta", "Alta"))
        else:
            alertas.append(_alerta_locacao(locacao, f"Devolucao prevista para {locacao.data_fim:%d/%m/%Y}.", "media", "Media"))

    return alertas


def _alerta_manutencao(ordem, mensagem, prioridade, prioridade_label):
    return {
        "tipo": "manutencao",
        "tipo_label": "Manutencao",
        "origem": ordem.codigo,
        "referencia": ordem.ativo.codigo,
        "mensagem": mensagem,
        "prazo": ordem.data_prevista,
        "prazo_label": "Previsao",
        "prioridade": prioridade,
        "prioridade_label": prioridade_label,
        "link": reverse("manutencao"),
    }


def _alerta_locacao(locacao, mensagem, prioridade, prioridade_label):
    return {
        "tipo": "locacao",
        "tipo_label": "Locacao",
        "origem": locacao.codigo,
        "referencia": locacao.cliente.nome,
        "mensagem": mensagem,
        "prazo": locacao.data_fim,
        "prazo_label": "Devolucao",
        "prioridade": prioridade,
        "prioridade_label": prioridade_label,
        "link": reverse("locacao_detail", kwargs={"pk": locacao.pk}),
    }
