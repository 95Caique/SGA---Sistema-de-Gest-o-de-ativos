from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from locacoes.models import ItemLocacao, Locacao

from .models import Rastreador


class RastreamentoViewTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaAtivo.objects.create(nome="Imagem")
        self.cliente = Cliente.objects.create(nome="Cliente Producao", documento="12345678000190")
        self.ativo = Ativo.objects.create(
            codigo="CAM-001",
            nome="Camera X",
            categoria=self.categoria,
            permite_rastreamento=True,
        )
        self.locacao = Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=date(2026, 7, 1),
            data_fim=date(2026, 7, 5),
            status=Locacao.Status.ATIVA,
        )
        ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("500.00"),
        )
        self.locacao.sincronizar_status_ativos()

    def test_mapa_exibe_locacao_ativa_do_rastreador(self):
        response = self.client.get(reverse("rastreamento"))

        self.assertContains(response, "Camera X")
        self.assertContains(response, "LOC-0001")
        self.assertContains(response, "Cliente Producao")
        self.assertContains(response, "Dados simulados")

    def test_mapa_filtra_por_status_do_rastreador(self):
        outro_ativo = Ativo.objects.create(
            codigo="MIC-001",
            nome="Microfone",
            categoria=self.categoria,
            permite_rastreamento=True,
        )
        Rastreador.objects.create(
            ativo=outro_ativo,
            identificador="SIM-MIC-001",
            status=Rastreador.Status.OFFLINE,
        )

        response = self.client.get(reverse("rastreamento"), {"status": Rastreador.Status.ONLINE})

        self.assertContains(response, "Camera X")
        self.assertNotContains(response, "Microfone")

    def test_mapa_exibe_locacao_ativa_sem_rastreamento(self):
        ativo_sem_rastreio = Ativo.objects.create(
            codigo="LAV-001",
            nome="Lavalier",
            categoria=self.categoria,
            permite_rastreamento=False,
        )
        locacao = Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=date(2026, 7, 10),
            data_fim=date(2026, 7, 12),
            status=Locacao.Status.ATIVA,
        )
        ItemLocacao.objects.create(
            locacao=locacao,
            ativo=ativo_sem_rastreio,
            quantidade=1,
            valor_diaria=Decimal("20.00"),
            valor_total=Decimal("60.00"),
        )

        response = self.client.get(reverse("rastreamento"))

        self.assertContains(response, "Locacoes ativas sem rastreamento")
        self.assertContains(response, "LOC-0002")
        self.assertContains(response, "Equipamento nao permite rastreamento")
