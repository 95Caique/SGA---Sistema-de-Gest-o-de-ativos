from django.test import TestCase
from django.urls import reverse

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente
from locacoes.models import Locacao
from manutencao.models import OrdemManutencao
from rastreamento.models import Rastreador


class RelatoriosListTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaAtivo.objects.create(nome="Construcao")
        self.ativo_disponivel = Ativo.objects.create(
            codigo="BET-001",
            nome="Betoneira 400L",
            categoria=self.categoria,
            status=Ativo.Status.DISPONIVEL,
        )
        self.ativo_locado = Ativo.objects.create(
            codigo="GER-001",
            nome="Gerador 65KVA",
            categoria=self.categoria,
            status=Ativo.Status.LOCADO,
            permite_rastreamento=True,
        )
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

    def test_exibe_indicadores_consolidados(self):
        self.criar_locacao("LOC-0001", Locacao.Status.ATIVA, "1200.00")
        self.criar_locacao("LOC-0002", Locacao.Status.FINALIZADA, "800.00")
        self.criar_locacao("LOC-0003", Locacao.Status.CANCELADA, "300.00")
        OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo_disponivel,
            descricao="Revisao",
        )

        response = self.client.get(reverse("relatorios"))

        self.assertContains(response, "R$ 2.000,00")
        self.assertContains(response, "50%")
        self.assertContains(response, "Manutencoes abertas")
        self.assertContains(response, "Construtora Forte")

    def test_exibe_status_de_rastreamento_e_categorias(self):
        Rastreador.objects.create(
            ativo=self.ativo_locado,
            identificador="SIM-GER-001",
            status=Rastreador.Status.SEM_COMUNICACAO,
        )

        response = self.client.get(reverse("relatorios"))

        self.assertContains(response, "Sem comunicacao")
        self.assertContains(response, "Construcao")
        self.assertContains(response, "2")
