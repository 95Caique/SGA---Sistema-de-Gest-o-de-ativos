from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from locacoes.models import Locacao


class FinanceiroListTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
        )

    def criar_locacao(
        self,
        codigo,
        status,
        valor_total,
        status_pagamento=Locacao.StatusPagamento.ABERTO,
        data_fim=None,
    ):
        data_fim = data_fim or timezone.localdate() + timedelta(days=5)
        return Locacao.objects.create(
            codigo=codigo,
            cliente=self.cliente,
            data_inicio=data_fim - timedelta(days=5),
            data_fim=data_fim,
            status=status,
            status_pagamento=status_pagamento,
            valor_total=valor_total,
        )

    def test_exibe_resumo_financeiro_das_locacoes(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA, "1200.00")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00", Locacao.StatusPagamento.RECEBIDO)
        self.criar_locacao("LOC-0003", Locacao.Status.CANCELADA, "300.00", Locacao.StatusPagamento.CANCELADO)

        response = self.client.get(reverse("financeiro"))

        self.assertContains(response, "R$ 2.000,00")
        self.assertContains(response, "R$ 1.200,00")
        self.assertContains(response, "R$ 800,00")
        self.assertContains(response, "R$ 300,00")

    def test_exibe_situacao_financeira_dos_lancamentos(self):
        hoje = timezone.localdate()
        self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00", data_fim=hoje - timedelta(days=1))
        self.criar_locacao("LOC-0002", Locacao.Status.ATIVA, "800.00", data_fim=hoje)
        self.criar_locacao("LOC-0003", Locacao.Status.AGENDADA, "300.00", data_fim=hoje + timedelta(days=5))

        response = self.client.get(reverse("financeiro"))

        self.assertContains(response, "Vencido")
        self.assertContains(response, "Vence hoje")
        self.assertContains(response, "A vencer")
        self.assertContains(response, "R$ 1.200,00")

    def test_filtra_lancamentos_vencidos(self):
        hoje = timezone.localdate()
        self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00", data_fim=hoje - timedelta(days=1))
        self.criar_locacao("LOC-0002", Locacao.Status.AGENDADA, "800.00", data_fim=hoje + timedelta(days=3))

        response = self.client.get(reverse("financeiro"), {"situacao": "vencido"})

        self.assertContains(response, "LOC-0001")
        self.assertNotContains(response, "LOC-0002")

    def test_filtra_lancamentos_em_aberto(self):
        self.criar_locacao("LOC-0001", Locacao.Status.AGENDADA, "1200.00")
        self.criar_locacao("LOC-0002", Locacao.Status.AGENDADA, "800.00", Locacao.StatusPagamento.RECEBIDO)

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

    def test_marca_pagamento_como_recebido(self):
        locacao = self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00")

        response = self.client.post(reverse("financeiro_receber", kwargs={"pk": locacao.pk}))

        locacao.refresh_from_db()
        self.assertRedirects(response, reverse("financeiro"))
        self.assertEqual(locacao.status_pagamento, Locacao.StatusPagamento.RECEBIDO)
        self.assertIsNotNone(locacao.data_pagamento)

    def test_reabre_pagamento_recebido(self):
        locacao = self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00", Locacao.StatusPagamento.RECEBIDO)
        locacao.data_pagamento = "2026-07-25"
        locacao.save()

        response = self.client.post(reverse("financeiro_reabrir", kwargs={"pk": locacao.pk}))

        locacao.refresh_from_db()
        self.assertRedirects(response, reverse("financeiro"))
        self.assertEqual(locacao.status_pagamento, Locacao.StatusPagamento.ABERTO)
        self.assertIsNone(locacao.data_pagamento)

    def test_nao_recebe_locacao_cancelada(self):
        locacao = self.criar_locacao("LOC-0001", Locacao.Status.CANCELADA, "1200.00", Locacao.StatusPagamento.CANCELADO)

        response = self.client.post(reverse("financeiro_receber", kwargs={"pk": locacao.pk}))

        locacao.refresh_from_db()
        self.assertRedirects(response, reverse("financeiro"))
        self.assertEqual(locacao.status_pagamento, Locacao.StatusPagamento.CANCELADO)
