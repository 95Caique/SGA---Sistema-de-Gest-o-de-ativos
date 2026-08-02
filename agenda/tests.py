from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from locacoes.models import Locacao


class AgendaListTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
        )

    def test_lista_entrega_e_devolucao_da_locacao(self):
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"))

        self.assertContains(response, "LOC-0001", count=2)
        self.assertContains(response, "Entrega")
        self.assertContains(response, "Devolucao")

    def test_filtra_eventos_por_tipo(self):
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"), {"tipo": "entrega"})

        self.assertContains(response, "Entrega")
        self.assertNotContains(response, "Devolucao")

    def test_nao_lista_locacao_cancelada(self):
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.CANCELADA,
        )

        response = self.client.get(reverse("agenda"))

        self.assertNotContains(response, "LOC-0001")
        self.assertContains(response, "Nenhum evento na agenda")

    def test_classifica_eventos_por_situacao(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje - timedelta(days=3),
            data_fim=hoje,
            status=Locacao.Status.ATIVA,
        )
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=hoje + timedelta(days=1),
            data_fim=hoje + timedelta(days=5),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"))

        self.assertContains(response, "Atrasado")
        self.assertContains(response, "Hoje")
        self.assertContains(response, "Proximo")
        self.assertContains(response, "Futuro")

    def test_filtra_eventos_por_situacao(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje - timedelta(days=3),
            data_fim=hoje - timedelta(days=1),
            status=Locacao.Status.ATIVA,
        )
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=hoje + timedelta(days=5),
            data_fim=hoje + timedelta(days=7),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"), {"situacao": "atrasado"})

        self.assertContains(response, "LOC-0001")
        self.assertNotContains(response, "LOC-0002")
