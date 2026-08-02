from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ativos.models import CategoriaAtivo
from clientes.models import Cliente
from locacoes.models import Locacao

from .views import _revenue_months


class DashboardTests(TestCase):
    def setUp(self):
        CategoriaAtivo.objects.create(nome="Audiovisual")
        self.cliente = Cliente.objects.create(nome="Cliente Teste", documento="12345678000190")

    def test_dashboard_usa_dados_reais_de_atrasos_e_devolucoes(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje - timedelta(days=5),
            data_fim=hoje - timedelta(days=1),
            status=Locacao.Status.ATIVA,
            valor_total="300.00",
        )
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=hoje - timedelta(days=1),
            data_fim=hoje,
            status=Locacao.Status.ATIVA,
            valor_total="150.00",
        )

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Locacoes atrasadas")
        self.assertContains(response, "Devolucoes hoje")
        self.assertContains(response, "R$ 300,00")
        self.assertContains(response, reverse("alertas"))
        self.assertContains(response, f"{reverse('agenda')}?situacao=hoje&amp;tipo=devolucao")

    def test_dashboard_locacoes_recentes_linkam_para_o_detalhe(self):
        locacao = Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=timezone.localdate(),
            data_fim=timezone.localdate(),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, reverse("locacao_detail", kwargs={"pk": locacao.pk}))
        self.assertNotContains(response, 'href="#"')

    def test_grafico_mensal_usa_receita_real_e_ignora_canceladas(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje,
            data_fim=hoje,
            status=Locacao.Status.FINALIZADA,
            valor_total="450.00",
        )
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=hoje,
            data_fim=hoje,
            status=Locacao.Status.CANCELADA,
            valor_total="999.00",
        )

        months = _revenue_months(hoje)

        self.assertEqual(months[-1]["amount"], "R$ 450,00")
        self.assertEqual(months[-1]["height"], 100)
