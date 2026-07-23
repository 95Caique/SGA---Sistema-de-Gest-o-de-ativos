from decimal import Decimal

from django.db.models import Count, Sum
from django.shortcuts import redirect, render

from ativos.models import Ativo
from clientes.models import Cliente
from locacoes.models import Locacao
from rastreamento.models import Rastreador


NAV_ITEMS = [
    {"label": "Dashboard", "url_name": "dashboard", "icon": "D"},
    {"label": "Agenda", "url_name": "agenda", "icon": "A"},
    {"label": "Locacoes", "url_name": "locacoes", "icon": "L"},
    {"label": "Orcamentos", "url_name": "orcamentos", "icon": "O"},
    {"label": "Equipamentos", "url_name": "equipamentos", "icon": "E"},
    {"label": "Clientes", "url_name": "clientes", "icon": "C"},
    {"label": "Contratos", "url_name": "contratos", "icon": "K"},
    {"label": "Financeiro", "url_name": "financeiro", "icon": "F"},
    {"label": "Manutencao", "url_name": "manutencao", "icon": "M"},
    {"label": "Rastreamento", "url_name": "rastreamento", "icon": "R"},
    {"label": "Alertas", "url_name": "alertas", "icon": "!"},
    {"label": "Relatorios", "url_name": "relatorios", "icon": "G"},
]


MODULES = {
    "agenda": {
        "title": "Agenda",
        "subtitle": "Entregas, retiradas, devolucoes e compromissos operacionais.",
        "primary_action": "Novo evento",
        "columns": ["Data", "Tipo", "Cliente", "Ativo", "Status"],
        "rows": [
            ["Hoje 09:00", "Entrega", "Construtora Forte", "Betoneira Menegotti 400L", "Agendada"],
            ["Hoje 14:30", "Devolucao", "Evento Music", "Gerador 65KVA", "Pendente"],
            ["Amanha 08:00", "Retirada", "TV Serra Dourada", "Camera Sony PXW-X70", "Confirmada"],
        ],
    },
    "locacoes": {
        "title": "Locacoes",
        "subtitle": "Pedidos de locacao, reservas, contratos e devolucoes.",
        "primary_action": "Nova locacao",
        "columns": ["Locacao", "Cliente", "Periodo", "Equipamentos", "Valor total", "Status"],
        "rows": [],
    },
    "equipamentos": {
        "title": "Equipamentos",
        "subtitle": "Cadastro e disponibilidade dos ativos locaveis.",
        "primary_action": "Novo equipamento",
        "columns": ["Codigo", "Equipamento", "Categoria", "Status", "Localizacao"],
        "rows": [
            ["BET-034", "Betoneira Menegotti 400L", "Construcao", "Locado", "Obra - Construtora Forte"],
            ["PROJ-012", "Projetor Epson PowerLite E20", "Audiovisual", "Disponivel", "Deposito Matriz"],
            ["GER-015", "Gerador Stemac 65KVA", "Energia", "Manutencao", "Oficina"],
            ["COMP-009", "Compactador Wacker DPU 80", "Construcao", "Disponivel", "Deposito Matriz"],
        ],
    },
    "clientes": {
        "title": "Clientes",
        "subtitle": "Cadastro, contatos e historico comercial.",
        "primary_action": "Novo cliente",
        "columns": ["Cliente", "Documento", "Contato", "Locacoes", "Status"],
        "rows": [
            ["Construtora Forte", "12.345.678/0001-90", "Mariana Alves", "18", "Ativo"],
            ["Alpha Eventos", "23.456.789/0001-10", "Rafael Costa", "9", "Ativo"],
            ["TV Serra Dourada", "34.567.890/0001-22", "Bianca Lima", "12", "Ativo"],
        ],
    },
    "contratos": {
        "title": "Contratos",
        "subtitle": "Contratos ativos, encerrados, vencidos e assinaturas.",
        "primary_action": "Novo contrato",
        "columns": ["Contrato", "Cliente", "Inicio", "Fim", "Valor total", "Status"],
        "rows": [
            ["CTR-0056", "Construtora Forte", "10/05/2025", "17/05/2025", "R$ 2.450,00", "Ativo"],
            ["CTR-0055", "TV Serra Dourada", "08/05/2025", "15/05/2025", "R$ 5.300,00", "Ativo"],
            ["CTR-0050", "Construtora Alianca", "01/05/2025", "06/05/2025", "R$ 850,00", "Encerrado"],
        ],
    },
    "financeiro": {
        "title": "Financeiro",
        "subtitle": "Recebimentos, pagamentos, fluxo de caixa e conciliacao.",
        "primary_action": "Novo titulo",
        "columns": ["Vencimento", "Descricao", "Cliente", "Valor", "Status"],
        "rows": [
            ["15/05/2025", "Locacao LOC-0058", "Construtora Forte", "R$ 2.450,00", "Aberto"],
            ["14/05/2025", "Locacao LOC-0057", "Alpha Eventos", "R$ 4.375,00", "Aberto"],
            ["09/05/2025", "Locacao LOC-0052", "Prefeitura de Goiania", "R$ 6.600,00", "Pendente"],
        ],
    },
    "manutencao": {
        "title": "Manutencao",
        "subtitle": "Ordens de servico, manutencoes preventivas e corretivas.",
        "primary_action": "Nova OS",
        "columns": ["OS", "Equipamento", "Tipo", "Tecnico", "Status", "Abertura"],
        "rows": [
            ["OS-0018", "Betoneira Menegotti 400L", "Preventiva", "Carlos Silva", "Em andamento", "12/05/2025"],
            ["OS-0017", "Gerador Stemac 65KVA", "Corretiva", "Joao Santos", "Em andamento", "10/05/2025"],
            ["OS-0015", "Compactador Wacker DPU 80", "Corretiva", "Carlos Silva", "Aguardando peca", "08/05/2025"],
        ],
    },
    "rastreamento": {
        "title": "Rastreamento",
        "subtitle": "Mapa operacional com dados simulados ate os rastreadores reais entrarem.",
        "primary_action": "Ver historico",
        "columns": ["Equipamento", "Cliente", "Movimento", "Ultima posicao", "Bateria", "Status"],
        "rows": [
            ["Betoneira 400L", "Construtora Forte", "23 km/h", "Av. Perimetral Norte", "85%", "Em movimento"],
            ["Projetor Epson E20", "Agencia Impacto", "Parado", "Setor Bueno", "92%", "Online"],
            ["Gerador 65KVA", "Evento Music", "Sem comunicacao", "Jardim America", "41%", "Alerta"],
        ],
    },
    "alertas": {
        "title": "Alertas",
        "subtitle": "Ocorrencias criticas de locacao, contrato, manutencao e rastreio.",
        "primary_action": "Novo alerta",
        "columns": ["Tipo", "Origem", "Mensagem", "Prioridade", "Status"],
        "rows": [
            ["Rastreamento", "GER-015", "Rastreador sem comunicacao ha 45 min", "Alta", "Aberto"],
            ["Contrato", "CTR-0056", "Contrato vence em 2 dias", "Media", "Aberto"],
            ["Manutencao", "BET-034", "Preventiva proxima do limite de horas", "Media", "Aberto"],
        ],
    },
    "relatorios": {
        "title": "Relatorios",
        "subtitle": "Indicadores de locacao, financeiro, estoque e desempenho dos ativos.",
        "primary_action": "Exportar",
        "columns": ["Relatorio", "Periodo", "Modulo", "Atualizacao", "Status"],
        "rows": [
            ["Faturamento por cliente", "Mensal", "Financeiro", "Hoje 08:20", "Pronto"],
            ["Disponibilidade de ativos", "Semanal", "Equipamentos", "Hoje 07:50", "Pronto"],
            ["Atrasos e devolucoes", "Diario", "Locacoes", "Hoje 07:30", "Pronto"],
        ],
    },
}


def with_layout(context):
    context["nav_items"] = NAV_ITEMS
    return context


def home(request):
    return redirect("dashboard")


def money_br(value):
    value = value or Decimal("0")
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def percent(value, total):
    if not total:
        return "0%"
    return f"{round((value / total) * 100)}%"


def dashboard_context():
    total_locacoes = Locacao.objects.count()
    locacoes_ativas = Locacao.objects.filter(status=Locacao.Status.ATIVA).count()
    locacoes_agendadas = Locacao.objects.filter(status=Locacao.Status.AGENDADA).count()
    locacoes_finalizadas = Locacao.objects.filter(status=Locacao.Status.FINALIZADA).count()
    locacoes_canceladas = Locacao.objects.filter(status=Locacao.Status.CANCELADA).count()
    faturamento_total = Locacao.objects.aggregate(total=Sum("valor_total"))["total"] or Decimal("0")
    valor_em_aberto = Locacao.objects.filter(status__in=[Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA]).aggregate(
        total=Sum("valor_total")
    )["total"] or Decimal("0")
    equipamentos_total = Ativo.objects.count()
    equipamentos_manutencao = Ativo.objects.filter(status=Ativo.Status.MANUTENCAO).count()
    clientes_ativos = Cliente.objects.filter(status=Cliente.Status.ATIVO).count()
    rastreadores_sem_comunicacao = Rastreador.objects.filter(status=Rastreador.Status.SEM_COMUNICACAO).count()

    recent_rentals = []
    for locacao in Locacao.objects.select_related("cliente").annotate(total_itens=Count("itens")).order_by("-data_inicio")[:5]:
        recent_rentals.append(
            {
                "code": locacao.codigo,
                "client": locacao.cliente.nome,
                "period": f"{locacao.data_inicio:%d/%m/%Y} - {locacao.data_fim:%d/%m/%Y}",
                "items": f"{locacao.total_itens} item{'s' if locacao.total_itens != 1 else ''}",
                "amount": money_br(locacao.valor_total),
                "status": locacao.get_status_display(),
                "status_key": locacao.status,
            }
        )

    return {
        "metrics": [
            {"label": "Faturamento", "value": money_br(faturamento_total), "trend": "Total registrado em locacoes", "tone": "success"},
            {"label": "Locacoes ativas", "value": locacoes_ativas, "trend": f"{total_locacoes} locacoes cadastradas", "tone": "success"},
            {"label": "Equipamentos", "value": equipamentos_total, "trend": f"{equipamentos_manutencao} em manutencao", "tone": "neutral"},
            {"label": "Clientes ativos", "value": clientes_ativos, "trend": "Clientes aptos para locacao", "tone": "warning"},
        ],
        "financial_summary": [
            {"label": "Receitas", "value": money_br(faturamento_total), "tone": "neutral"},
            {"label": "Despesas", "value": money_br(Decimal("0")), "tone": "neutral"},
            {"label": "A receber", "value": money_br(valor_em_aberto), "tone": "warning"},
            {"label": "Atrasados", "value": money_br(Decimal("0")), "tone": "danger"},
        ],
        "rental_status": [
            {"label": "Ativas", "value": locacoes_ativas, "percent": percent(locacoes_ativas, total_locacoes), "color": "purple"},
            {"label": "Agendadas", "value": locacoes_agendadas, "percent": percent(locacoes_agendadas, total_locacoes), "color": "green"},
            {"label": "Finalizadas", "value": locacoes_finalizadas, "percent": percent(locacoes_finalizadas, total_locacoes), "color": "yellow"},
            {"label": "Canceladas", "value": locacoes_canceladas, "percent": percent(locacoes_canceladas, total_locacoes), "color": "red"},
        ],
        "alert_cards": [
            {"label": "Equip. em manutencao", "value": equipamentos_manutencao, "action": "Ver detalhes", "tone": "purple"},
            {"label": "Equip. sem comunicacao", "value": rastreadores_sem_comunicacao, "action": "Ver no mapa", "tone": "danger"},
            {"label": "Contratos vencendo", "value": 0, "action": "Ver contratos", "tone": "warning"},
            {"label": "Devolucoes hoje", "value": 0, "action": "Ver agenda", "tone": "success"},
        ],
        "recent_rentals": recent_rentals,
    }


def dashboard(request):
    context = dashboard_context()
    context["page_title"] = "Dashboard"
    return render(
        request,
        "pages/dashboard.html",
        with_layout(context),
    )


def module_page(request, module):
    data = MODULES[module]
    return render(request, "pages/module.html", with_layout({"page_title": data["title"], "module": data}))
