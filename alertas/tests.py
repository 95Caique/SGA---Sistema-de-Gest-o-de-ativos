from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from locacoes.models import Locacao
from manutencao.models import OrdemManutencao
from rastreamento.models import Rastreador


class AlertasListTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaAtivo.objects.create(nome="Construcao")
        self.ativo = Ativo.objects.create(
            codigo="BET-001",
            nome="Betoneira 400L",
            categoria=self.categoria,
            status=Ativo.Status.DISPONIVEL,
            permite_rastreamento=True,
        )
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
        )

    def test_exibe_alerta_de_rastreador_sem_comunicacao(self):
        Rastreador.objects.create(
            ativo=self.ativo,
            identificador="SIM-BET-001",
            status=Rastreador.Status.SEM_COMUNICACAO,
        )

        response = self.client.get(reverse("alertas"))

        self.assertContains(response, "Rastreador sem comunicacao.")
        self.assertContains(response, "BET-001")

    def test_exibe_alerta_de_manutencao_alta_aberta(self):
        OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            prioridade=OrdemManutencao.Prioridade.ALTA,
            descricao="Falha critica",
        )

        response = self.client.get(reverse("alertas"))

        self.assertContains(response, "Manutencao de alta prioridade em aberto.")
        self.assertContains(response, "MAN-0001")

    def test_exibe_alerta_de_devolucao_proxima(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=1),
            status=Locacao.Status.ATIVA,
        )

        response = self.client.get(reverse("alertas"))

        self.assertContains(response, "Devolucao prevista")
        self.assertContains(response, "LOC-0001")

    def test_filtra_alertas_por_tipo(self):
        OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            prioridade=OrdemManutencao.Prioridade.ALTA,
            descricao="Falha critica",
        )
        Rastreador.objects.create(
            ativo=self.ativo,
            identificador="SIM-BET-001",
            status=Rastreador.Status.SEM_COMUNICACAO,
        )

        response = self.client.get(reverse("alertas"), {"tipo": "manutencao"})

        self.assertContains(response, "MAN-0001")
        self.assertNotContains(response, "Rastreador sem comunicacao.")
