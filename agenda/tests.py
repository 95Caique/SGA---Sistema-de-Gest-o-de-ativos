from django.test import TestCase
from django.urls import reverse

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
