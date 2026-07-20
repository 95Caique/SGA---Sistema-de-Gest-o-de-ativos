from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from locacoes.models import Locacao


class FinanceiroListTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
        )

    def criar_locacao(self, codigo, status, valor_total):
        return Locacao.objects.create(
            codigo=codigo,
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=status,
            valor_total=valor_total,
        )

    def test_exibe_resumo_financeiro_das_locacoes(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA, "1200.00")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00")
        self.criar_locacao("LOC-0003", Locacao.Status.CANCELADA, "300.00")

        response = self.client.get(reverse("financeiro"))

        self.assertContains(response, "R$ 2.000,00")
        self.assertContains(response, "R$ 1.200,00")
        self.assertContains(response, "R$ 800,00")
        self.assertContains(response, "R$ 300,00")

    def test_filtra_lancamentos_em_aberto(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA, "1200.00")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00")

        response = self.client.get(reverse("financeiro"), {"status": "aberto"})

        self.assertContains(response, "LOC-0001")
        self.assertNotContains(response, "LOC-0002")

    def test_busca_por_cliente(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA, "1200.00")
        outro_cliente = Cliente.objects.create(nome="Alpha Eventos", documento="23.456.789/0001-10")
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=outro_cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.AGENDADA,
            valor_total="800.00",
        )

        response = self.client.get(reverse("financeiro"), {"q": "Alpha"})

        self.assertContains(response, "LOC-0002")
        self.assertNotContains(response, "LOC-0001")
