from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from locacoes.models import ItemLocacao, Locacao


class ContratosListTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
        )
        self.categoria = CategoriaAtivo.objects.create(nome="Construcao")
        self.ativo = Ativo.objects.create(
            codigo="BET-001",
            nome="Betoneira 400L",
            categoria=self.categoria,
        )

    def criar_locacao(self, codigo, status, data_inicio=None, data_fim=None):
        hoje = timezone.localdate()
        return Locacao.objects.create(
            codigo=codigo,
            cliente=self.cliente,
            data_inicio=data_inicio or hoje,
            data_fim=data_fim or hoje + timedelta(days=5),
            status=status,
            valor_total="1200.00",
        )

    def test_lista_contratos_gerados_por_locacoes(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA)

        response = self.client.get(reverse("contratos"))

        self.assertContains(response, "CTR-LOC-0001")
        self.assertContains(response, "Construtora Forte")
        self.assertContains(response, "Ativo")
        self.assertContains(response, "PDF")

    def test_filtra_contratos_vencidos(self):
        hoje = timezone.localdate()
        self.criar_locacao(
            "LOC-0001",
            Locacao.Status.ATIVA,
            data_inicio=hoje - timedelta(days=10),
            data_fim=hoje - timedelta(days=1),
        )
        self.criar_locacao("LOC-0002", Locacao.Status.AGENDADA)

        response = self.client.get(reverse("contratos"), {"status": "vencido"})

        self.assertContains(response, "CTR-LOC-0001")
        self.assertContains(response, "Vencido")
        self.assertContains(response, "1 dia(s) em atraso")
        self.assertNotContains(response, "CTR-LOC-0002")

    def test_lista_contrato_vencendo_em_breve(self):
        hoje = timezone.localdate()
        self.criar_locacao(
            "LOC-0001",
            Locacao.Status.ATIVA,
            data_inicio=hoje - timedelta(days=2),
            data_fim=hoje + timedelta(days=2),
        )

        response = self.client.get(reverse("contratos"))

        self.assertContains(response, "Vence em 2 dia(s)")

    def test_resumo_de_contratos_ignora_cancelados_no_valor(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA)
        self.criar_locacao("LOC-0002", Locacao.Status.CANCELADA)

        response = self.client.get(reverse("contratos"))

        self.assertContains(response, "Valor contratado")
        self.assertContains(response, "R$ 1.200,00")
        self.assertContains(response, "Contratos ativos")

    def test_busca_contrato_por_cliente(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA)
        outro_cliente = Cliente.objects.create(nome="Alpha Eventos", documento="23.456.789/0001-10")
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=outro_cliente,
            data_inicio=timezone.localdate(),
            data_fim=timezone.localdate() + timedelta(days=5),
            status=Locacao.Status.AGENDADA,
            valor_total="800.00",
        )

        response = self.client.get(reverse("contratos"), {"q": "Alpha"})

        self.assertContains(response, "CTR-LOC-0002")
        self.assertNotContains(response, "CTR-LOC-0001")

    @patch("wkhtmltopdf.views.render_pdf_from_template", return_value=b"%PDF-1.4")
    def test_gera_pdf_do_contrato(self, _render_pdf):
        locacao = self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA)
        ItemLocacao.objects.create(
            locacao=locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("500.00"),
        )

        response = self.client.get(reverse("contrato_pdf", kwargs={"pk": locacao.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertIn("contrato-LOC-0001.pdf", response["Content-Disposition"])

    def test_pdf_contrato_bloqueia_orcamento(self):
        locacao = self.criar_locacao("LOC-0001", Locacao.Status.ORCAMENTO)

        response = self.client.get(reverse("contrato_pdf", kwargs={"pk": locacao.pk}))

        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": locacao.pk}))
