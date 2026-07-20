from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.shortcuts import render

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from config.views import money_br, percent, with_layout
from locacoes.models import Locacao
from manutencao.models import OrdemManutencao
from rastreamento.models import Rastreador


def relatorios_list(request):
    total_ativos = Ativo.objects.count()
    ativos_disponiveis = Ativo.objects.filter(status=Ativo.Status.DISPONIVEL).count()
    locacoes_validas = Locacao.objects.exclude(status=Locacao.Status.CANCELADA)
    faturamento_previsto = locacoes_validas.aggregate(total=Sum("valor_total"))["total"] or Decimal("0")

    indicadores = [
        {
            "label": "Faturamento previsto",
            "value": money_br(faturamento_previsto),
            "trend": "Locacoes nao canceladas",
            "tone": "success",
        },
        {
            "label": "Locacoes ativas",
            "value": Locacao.objects.filter(status=Locacao.Status.ATIVA).count(),
            "trend": f"{Locacao.objects.count()} locacoes cadastradas",
            "tone": "success",
        },
        {
            "label": "Disponibilidade",
            "value": percent(ativos_disponiveis, total_ativos),
            "trend": f"{ativos_disponiveis} de {total_ativos} equipamentos",
            "tone": "neutral",
        },
        {
            "label": "Manutencoes abertas",
            "value": OrdemManutencao.objects.filter(
                status__in=[OrdemManutencao.Status.ABERTA, OrdemManutencao.Status.EM_ANDAMENTO]
            ).count(),
            "trend": "Ordens em aberto ou andamento",
            "tone": "warning",
        },
    ]

    clientes = (
        Cliente.objects.annotate(
            receita=Sum("locacoes__valor_total", filter=~Q(locacoes__status=Locacao.Status.CANCELADA)),
            total_locacoes=Count("locacoes", filter=~Q(locacoes__status=Locacao.Status.CANCELADA)),
        )
        .filter(receita__gt=0)
        .order_by("-receita", "nome")[:5]
    )
    clientes_receita = [
        {
            "nome": cliente.nome,
            "documento": cliente.documento,
            "receita": money_br(cliente.receita),
            "total_locacoes": cliente.total_locacoes,
        }
        for cliente in clientes
    ]

    return render(
        request,
        "relatorios/list.html",
        with_layout(
            {
                "page_title": "Relatorios",
                "indicadores": indicadores,
                "locacoes_status": _status_locacoes(),
                "ativos_status": _status_ativos(total_ativos),
                "clientes_receita": clientes_receita,
                "categorias": CategoriaAtivo.objects.annotate(total_ativos=Count("ativos")).order_by(
                    "-total_ativos", "nome"
                )[:5],
                "rastreadores": _rastreamento_resumo(),
            }
        ),
    )


def _status_locacoes():
    total = Locacao.objects.count()
    return [
        {
            "label": label,
            "status": status,
            "count": Locacao.objects.filter(status=status).count(),
            "percent": percent(Locacao.objects.filter(status=status).count(), total),
        }
        for status, label in Locacao.Status.choices
    ]


def _status_ativos(total):
    return [
        {
            "label": label,
            "status": status,
            "count": Ativo.objects.filter(status=status).count(),
            "percent": percent(Ativo.objects.filter(status=status).count(), total),
        }
        for status, label in Ativo.Status.choices
    ]


def _rastreamento_resumo():
    return {
        "total": Rastreador.objects.count(),
        "online": Rastreador.objects.filter(status=Rastreador.Status.ONLINE).count(),
        "sem_comunicacao": Rastreador.objects.filter(status=Rastreador.Status.SEM_COMUNICACAO).count(),
    }
