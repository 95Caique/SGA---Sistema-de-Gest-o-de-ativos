from django.shortcuts import redirect, render


NAV_ITEMS = [
    {"label": "Dashboard", "url_name": "dashboard", "icon": "D"},
    {"label": "Agenda", "url_name": "agenda", "icon": "A"},
    {"label": "Locacoes", "url_name": "locacoes", "icon": "L"},
    {"label": "Equipamentos", "url_name": "equipamentos", "icon": "E"},
    {"label": "Clientes", "url_name": "clientes", "icon": "C"},
    {"label": "Contratos", "url_name": "contratos", "icon": "K"},
    {"label": "Financeiro", "url_name": "financeiro", "icon": "F"},
    {"label": "Manutencao", "url_name": "manutencao", "icon": "M"},
    {"label": "Rastreamento", "url_name": "rastreamento", "icon": "R"},
    {"label": "Alertas", "url_name": "alertas", "icon": "!"},
    {"label": "Relatorios", "url_name": "relatorios", "icon": "G"},
]


DASHBOARD_METRICS = [
    {"label": "Faturamento", "value": "R$ 128.690,00", "trend": "+18,5% vs mes anterior", "tone": "success"},
    {"label": "Locacoes ativas", "value": "87", "trend": "+12% vs mes anterior", "tone": "success"},
    {"label": "Equipamentos", "value": "248", "trend": "Transporte 15", "tone": "neutral"},
    {"label": "Clientes ativos", "value": "56", "trend": "+8% vs mes anterior", "tone": "warning"},
]


FINANCIAL_SUMMARY = [
    {"label": "Receitas", "value": "R$ 128.690,00", "tone": "neutral"},
    {"label": "Despesas", "value": "R$ 34.560,00", "tone": "neutral"},
    {"label": "A receber", "value": "R$ 45.230,00", "tone": "warning"},
    {"label": "Atrasados", "value": "R$ 12.450,00", "tone": "danger"},
]


RENTAL_STATUS = [
    {"label": "Ativas", "value": "87", "percent": "65%", "color": "purple"},
    {"label": "Agendadas", "value": "32", "percent": "24%", "color": "green"},
    {"label": "Finalizadas", "value": "12", "percent": "9%", "color": "yellow"},
    {"label": "Canceladas", "value": "2", "percent": "2%", "color": "red"},
]


ALERT_CARDS = [
    {"label": "Equip. em manutencao", "value": "6", "action": "Ver detalhes", "tone": "purple"},
    {"label": "Equip. sem comunicacao", "value": "3", "action": "Ver no mapa", "tone": "danger"},
    {"label": "Contratos vencendo", "value": "9", "action": "Ver contratos", "tone": "warning"},
    {"label": "Devolucoes hoje", "value": "4", "action": "Ver agenda", "tone": "success"},
]


RECENT_RENTALS = [
    {"code": "LOC-0058", "client": "Construtora Forte", "period": "10/05/2025 - 17/05/2025", "items": "5 itens", "amount": "R$ 2.450,00", "status": "Ativa"},
    {"code": "LOC-0057", "client": "Alpha Eventos", "period": "08/05/2025 - 11/05/2025", "items": "12 itens", "amount": "R$ 8.750,00", "status": "Ativa"},
    {"code": "LOC-0056", "client": "TV Serra Dourada", "period": "08/05/2025 - 15/05/2025", "items": "7 itens", "amount": "R$ 5.300,00", "status": "Ativa"},
    {"code": "LOC-0055", "client": "Agencia Impacto", "period": "06/05/2025 - 10/05/2025", "items": "3 itens", "amount": "R$ 1.250,00", "status": "Ativa"},
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
        "rows": [[item["code"], item["client"], item["period"], item["items"], item["amount"], item["status"]] for item in RECENT_RENTALS],
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


def dashboard(request):
    return render(
        request,
        "pages/dashboard.html",
        with_layout(
            {
                "page_title": "Dashboard",
                "metrics": DASHBOARD_METRICS,
                "financial_summary": FINANCIAL_SUMMARY,
                "rental_status": RENTAL_STATUS,
                "alert_cards": ALERT_CARDS,
                "recent_rentals": RECENT_RENTALS,
            }
        ),
    )


def module_page(request, module):
    data = MODULES[module]
    return render(request, "pages/module.html", with_layout({"page_title": data["title"], "module": data}))
