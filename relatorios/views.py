import csv
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.dateparse import parse_date
from wkhtmltopdf.views import PDFTemplateResponse

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from config.views import money_br, percent, with_layout
from locacoes.models import Locacao
from manutencao.models import OrdemManutencao
from rastreamento.models import Rastreador


PDF_OPTIONS = {
    "quiet": True,
    "encoding": "utf8",
    "enable_local_file_access": True,
}


def relatorios_list(request):
    filters = _period_filters(request)
    context = _report_context(filters)

    return render(
        request,
        "relatorios/list.html",
        with_layout(context),
    )


def relatorios_export_pdf(request):
    filters = _period_filters(request)
    filename = "relatorio-operacional.pdf"

    return PDFTemplateResponse(
        request=request,
        template="relatorios/pdf.html",
        context=_report_context(filters),
        filename=filename,
        show_content_in_browser=True,
        cmd_options=PDF_OPTIONS,
    )


def relatorios_export_csv(request):
    filters = _period_filters(request)
    locacoes = _locacoes_exportacao(filters)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="relatorio-locacoes.csv"'
    writer = csv.writer(response)
    writer.writerow(["Codigo", "Cliente", "Inicio", "Fim", "Status", "Pagamento", "Valor total"])

    for locacao in locacoes:
        writer.writerow(
            [
                locacao.codigo,
                locacao.cliente.nome,
                locacao.data_inicio.strftime("%d/%m/%Y"),
                locacao.data_fim.strftime("%d/%m/%Y"),
                locacao.get_status_display(),
                locacao.get_status_pagamento_display(),
                str(locacao.valor_total),
            ]
        )

    return response


def _report_context(filters):
    locacoes_periodo = _locacoes_no_periodo(filters)
    total_ativos = Ativo.objects.count()
    ativos_disponiveis = Ativo.objects.filter(status=Ativo.Status.DISPONIVEL).count()
    locacoes_validas = locacoes_periodo.exclude(status=Locacao.Status.CANCELADA)
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
            "value": locacoes_periodo.filter(status=Locacao.Status.ATIVA).count(),
            "trend": f"{locacoes_periodo.count()} locacoes no periodo",
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
            receita=Sum("locacoes__valor_total", filter=_locacoes_cliente_filter(filters)),
            total_locacoes=Count("locacoes", filter=_locacoes_cliente_filter(filters)),
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

    return {
        "page_title": "Relatorios",
        "indicadores": indicadores,
        "locacoes_status": _status_locacoes(locacoes_periodo),
        "ativos_status": _status_ativos(total_ativos),
        "clientes_receita": clientes_receita,
        "categorias": CategoriaAtivo.objects.annotate(total_ativos=Count("ativos")).order_by(
            "-total_ativos", "nome"
        )[:5],
        "rastreadores": _rastreamento_resumo(),
        "filters": filters,
        "export_csv_url": _export_url(filters, "relatorios_export_csv"),
        "export_pdf_url": _export_url(filters, "relatorios_export_pdf"),
        "locacoes_exportacao": _locacoes_exportacao(filters),
    }


def _status_locacoes(locacoes):
    total = locacoes.count()
    return [
        {
            "label": label,
            "status": status,
            "count": locacoes.filter(status=status).count(),
            "percent": percent(locacoes.filter(status=status).count(), total),
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


def _period_filters(request):
    data_inicio = parse_date(request.GET.get("inicio", ""))
    data_fim = parse_date(request.GET.get("fim", ""))

    if data_inicio and data_fim and data_fim < data_inicio:
        data_inicio, data_fim = data_fim, data_inicio

    return {
        "inicio": data_inicio,
        "fim": data_fim,
        "inicio_value": data_inicio.isoformat() if data_inicio else "",
        "fim_value": data_fim.isoformat() if data_fim else "",
    }


def _locacoes_no_periodo(filters):
    locacoes = Locacao.objects.all()

    if filters["inicio"]:
        locacoes = locacoes.filter(data_inicio__gte=filters["inicio"])

    if filters["fim"]:
        locacoes = locacoes.filter(data_inicio__lte=filters["fim"])

    return locacoes


def _locacoes_exportacao(filters):
    return (
        _locacoes_no_periodo(filters)
        .select_related("cliente")
        .exclude(status=Locacao.Status.CANCELADA)
        .order_by("data_inicio", "codigo")
    )


def _locacoes_cliente_filter(filters):
    query = ~Q(locacoes__status=Locacao.Status.CANCELADA)

    if filters["inicio"]:
        query &= Q(locacoes__data_inicio__gte=filters["inicio"])

    if filters["fim"]:
        query &= Q(locacoes__data_inicio__lte=filters["fim"])

    return query


def _export_url(filters, url_name):
    params = []

    if filters["inicio_value"]:
        params.append(f"inicio={filters['inicio_value']}")

    if filters["fim_value"]:
        params.append(f"fim={filters['fim_value']}")

    query = f"?{'&'.join(params)}" if params else ""
    return f"{reverse(url_name)}{query}"
