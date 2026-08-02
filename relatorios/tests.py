from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from locacoes.models import Locacao
from manutencao.models import OrdemManutencao
from rastreamento.models import Rastreador


class RelatoriosListTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaAtivo.objects.create(nome="Construcao")
        self.ativo_disponivel = Ativo.objects.create(
            codigo="BET-001",
            nome="Betoneira 400L",
            categoria=self.categoria,
            status=Ativo.Status.DISPONIVEL,
        )
        self.ativo_locado = Ativo.objects.create(
            codigo="GER-001",
            nome="Gerador 65KVA",
            categoria=self.categoria,
            status=Ativo.Status.LOCADO,
            permite_rastreamento=True,
        )
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
        )

    def criar_locacao(self, codigo, status, valor_total, data_inicio="2026-07-20"):
        return Locacao.objects.create(
            codigo=codigo,
            cliente=self.cliente,
            data_inicio=data_inicio,
            data_fim="2026-07-25",
            status=status,
            valor_total=valor_total,
        )

    def test_exibe_indicadores_consolidados(self):
        self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00")
        self.criar_locacao("LOC-0003", Locacao.Status.CANCELADA, "300.00")
        OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo_disponivel,
            descricao="Revisao",
        )

        response = self.client.get(reverse("relatorios"))

        self.assertContains(response, "R$ 2.000,00")
        self.assertContains(response, "50%")
        self.assertContains(response, "Manutencoes abertas")
        self.assertContains(response, "Construtora Forte")

    def test_exibe_status_de_rastreamento_e_categorias(self):
        Rastreador.objects.create(
            ativo=self.ativo_locado,
            identificador="SIM-GER-001",
            status=Rastreador.Status.SEM_COMUNICACAO,
        )

        response = self.client.get(reverse("relatorios"))

        self.assertContains(response, "Sem comunicacao")
        self.assertContains(response, "Construcao")
        self.assertContains(response, "2")

    def test_filtra_relatorio_por_periodo_da_locacao(self):
        self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00", data_inicio="2026-07-20")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00", data_inicio="2026-08-10")

        response = self.client.get(reverse("relatorios"), {"inicio": "2026-08-01", "fim": "2026-08-31"})

        self.assertContains(response, "R$ 800,00")
        self.assertNotContains(response, "R$ 2.000,00")
        self.assertContains(response, "2026-08-01")
        self.assertContains(response, "2026-08-31")
        self.assertContains(response, f"{reverse('relatorios_export_pdf')}?inicio=2026-08-01&amp;fim=2026-08-31")

    def test_exporta_relatorio_csv_respeitando_periodo(self):
        self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00", data_inicio="2026-07-20")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00", data_inicio="2026-08-10")

        response = self.client.get(reverse("relatorios_export_csv"), {"inicio": "2026-08-01", "fim": "2026-08-31"})
        content = response.content.decode()

        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn('attachment; filename="relatorio-locacoes.csv"', response["Content-Disposition"])
        self.assertIn("Codigo,Cliente,Inicio,Fim,Status,Pagamento,Valor total", content)
        self.assertIn("LOC-0002", content)
        self.assertNotIn("LOC-0001", content)

    @patch("wkhtmltopdf.views.render_pdf_from_template", return_value=b"%PDF-1.4")
    def test_exporta_relatorio_pdf_respeitando_periodo(self, _render_pdf):
        self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00", data_inicio="2026-07-20")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00", data_inicio="2026-08-10")

        response = self.client.get(reverse("relatorios_export_pdf"), {"inicio": "2026-08-01", "fim": "2026-08-31"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertIn("relatorio-operacional.pdf", response["Content-Disposition"])
