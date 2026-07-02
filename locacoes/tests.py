from datetime import date
from decimal import Decimal

from django.test import TestCase

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from rastreamento.models import Rastreador

from .models import ItemLocacao, Locacao


class LocacaoOperacaoTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaAtivo.objects.create(nome="Construcao")
        self.cliente = Cliente.objects.create(
            nome="Cliente Teste",
            documento="12345678000190",
        )
        self.ativo = Ativo.objects.create(
            codigo="BET-001",
            nome="Betoneira 400L",
            categoria=self.categoria,
            permite_rastreamento=True,
        )
        self.locacao = Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=date(2026, 7, 1),
            data_fim=date(2026, 7, 5),
            valor_servicos=Decimal("50.00"),
            valor_desconto=Decimal("10.00"),
        )

    def test_recalcula_totais_da_locacao(self):
        ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("400.00"),
        )

        self.locacao.recalcular_totais()
        self.locacao.refresh_from_db()

        self.assertEqual(self.locacao.valor_equipamentos, Decimal("400.00"))
        self.assertEqual(self.locacao.valor_total, Decimal("440.00"))

    def test_ativar_locacao_marca_ativo_locado_e_cria_rastreador_simulado(self):
        ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("400.00"),
        )
        self.locacao.status = Locacao.Status.ATIVA
        self.locacao.save()

        self.locacao.sincronizar_status_ativos()
        self.ativo.refresh_from_db()

        rastreador = Rastreador.objects.get(ativo=self.ativo)
        self.assertEqual(self.ativo.status, Ativo.Status.LOCADO)
        self.assertEqual(rastreador.identificador, "SIM-BET-001")
        self.assertEqual(rastreador.status, Rastreador.Status.ONLINE)
        self.assertTrue(rastreador.usando_dados_simulados)

    def test_finalizar_locacao_libera_ativo_e_deixa_rastreador_offline(self):
        ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("400.00"),
        )
        self.locacao.status = Locacao.Status.ATIVA
        self.locacao.save()
        self.locacao.sincronizar_status_ativos()

        self.locacao.finalizar_operacao()
        self.ativo.refresh_from_db()
        rastreador = Rastreador.objects.get(ativo=self.ativo)

        self.assertEqual(self.ativo.status, Ativo.Status.DISPONIVEL)
        self.assertEqual(rastreador.status, Rastreador.Status.OFFLINE)
