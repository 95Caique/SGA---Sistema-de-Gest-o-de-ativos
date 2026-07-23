from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from locacoes.models import Locacao


class ContratosListTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
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
        self.assertNotContains(response, "CTR-LOC-0002")

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
