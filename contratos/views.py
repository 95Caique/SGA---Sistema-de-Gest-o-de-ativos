from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from wkhtmltopdf.views import PDFTemplateResponse

from configuracoes.services import empresa_atual
from config.views import money_br, with_layout
from locacoes.models import Locacao


CONTRATO_STATUS_FILTROS = ["minuta", "ativo", "vencido", "encerrado", "cancelado"]
PDF_STATUS_BLOQUEADOS = [Locacao.Status.ORCAMENTO, Locacao.Status.CANCELADA]
PDF_OPTIONS = {
    "quiet": True,
    "encoding": "utf8",
    "enable_local_file_access": True,
}


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
    status_counts = _status_counts(contratos)

    if status_filter in CONTRATO_STATUS_FILTROS:
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
                "status_counts": status_counts,
                "resumo": _resumo_contratos(status_counts, contratos),
            }
        ),
    )


def contrato_pdf(request, pk):
    locacao = get_object_or_404(Locacao.objects.select_related("cliente", "endereco_entrega"), pk=pk)

    if locacao.status in PDF_STATUS_BLOQUEADOS:
        messages.error(request, "Contrato disponivel apenas para locacoes agendadas, ativas ou finalizadas.")
        return redirect("locacao_detail", pk=locacao.pk)

    itens = locacao.itens.select_related("ativo", "ativo__categoria").order_by("ativo__codigo")
    filename = f"contrato-{locacao.codigo}.pdf"

    return PDFTemplateResponse(
        request=request,
        template="contratos/pdf.html",
        context={
            "contrato": _contrato_from_locacao(locacao),
            "locacao": locacao,
            "itens": itens,
            "empresa": empresa_atual(),
            "data_emissao": timezone.localdate(),
            "periodo_dias": max((locacao.data_fim - locacao.data_inicio).days + 1, 1),
        },
        filename=filename,
        show_content_in_browser=True,
        cmd_options=PDF_OPTIONS,
    )


def _contrato_from_locacao(locacao):
    status_key, status_label = _status_contrato(locacao)
    vencimento = _vencimento_contrato(locacao, status_key)
    return {
        "codigo": f"CTR-{locacao.codigo}",
        "locacao": locacao,
        "cliente": locacao.cliente,
        "inicio": locacao.data_inicio,
        "fim": locacao.data_fim,
        "vencimento_label": vencimento["label"],
        "vencimento_tone": vencimento["tone"],
        "total_itens": getattr(locacao, "total_itens", locacao.itens.count()),
        "valor_decimal": locacao.valor_total,
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


def _vencimento_contrato(locacao, status_key):
    hoje = timezone.localdate()
    dias = (locacao.data_fim - hoje).days

    if status_key == "vencido":
        return {"label": f"{abs(dias)} dia(s) em atraso", "tone": "danger"}
    if status_key in ["encerrado", "cancelado"]:
        return {"label": locacao.data_fim.strftime("%d/%m/%Y"), "tone": "neutral"}
    if status_key == "minuta":
        return {"label": "Aguardando aprovacao", "tone": "warning"}
    if dias == 0:
        return {"label": "Vence hoje", "tone": "warning"}
    if dias <= 2:
        return {"label": f"Vence em {dias} dia(s)", "tone": "warning"}

    return {"label": f"{dias} dia(s) restantes", "tone": "success"}


def _status_counts(contratos):
    counts = {status: 0 for status in CONTRATO_STATUS_FILTROS}

    for contrato in contratos:
        counts[contrato["status_key"]] += 1

    return {
        "todos": len(contratos),
        "minutas": counts["minuta"],
        "ativos": counts["ativo"],
        "vencidos": counts["vencido"],
        "encerrados": counts["encerrado"],
        "cancelados": counts["cancelado"],
    }


def _resumo_contratos(counts, contratos):
    return {
        "valor_total": money_br(
            sum(contrato["valor_decimal"] for contrato in contratos if contrato["status_key"] != "cancelado")
        ),
        "ativos": counts["ativos"],
        "vencidos": counts["vencidos"],
        "minutas": counts["minutas"],
    }
