from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from locacoes.models import ItemLocacao, Locacao

from .models import Ativo, CategoriaAtivo


class EquipamentoViewTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaAtivo.objects.create(nome="Construcao")
        self.ativo = Ativo.objects.create(
            codigo="BET-001",
            patrimonio="PAT-001",
            nome="Betoneira 400L",
            categoria=self.categoria,
            status=Ativo.Status.DISPONIVEL,
        )

    def test_edita_equipamento(self):
        response = self.client.post(
            reverse("equipamento_update", kwargs={"pk": self.ativo.pk}),
            data={
                "codigo": "BET-001",
                "patrimonio": "PAT-001",
                "nome": "Betoneira 400L revisada",
                "categoria": self.categoria.pk,
                "nova_categoria": "",
                "status": Ativo.Status.MANUTENCAO,
                "localizacao_atual": "Oficina",
                "permite_rastreamento": "on",
                "horimetro_atual": "10.0",
                "proxima_manutencao_horas": "",
                "observacoes": "",
            },
        )

        self.ativo.refresh_from_db()
        self.assertRedirects(response, reverse("equipamentos"))
        self.assertEqual(self.ativo.nome, "Betoneira 400L revisada")
        self.assertEqual(self.ativo.status, Ativo.Status.MANUTENCAO)
        self.assertEqual(self.ativo.localizacao_atual, "Oficina")
        self.assertTrue(self.ativo.permite_rastreamento)

    def test_lista_equipamentos_filtra_por_status(self):
        Ativo.objects.create(
            codigo="RET-001",
            nome="Retroescavadeira",
            categoria=self.categoria,
            status=Ativo.Status.LOCADO,
        )

        response = self.client.get(reverse("equipamentos"), {"status": Ativo.Status.LOCADO})

        self.assertContains(response, "RET-001")
        self.assertNotContains(response, "BET-001")

    def test_lista_equipamentos_exibe_locacao_ativa_do_ativo_locado(self):
        cliente = Cliente.objects.create(nome="Cliente Obra", documento="12345678000190")
        locacao = Locacao.objects.create(
            codigo="LOC-0001",
            cliente=cliente,
            data_inicio="2026-07-01",
            data_fim="2026-07-05",
            status=Locacao.Status.ATIVA,
        )
        ItemLocacao.objects.create(
            locacao=locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria="100.00",
            valor_total="500.00",
        )
        self.ativo.status = Ativo.Status.LOCADO
        self.ativo.save()

        response = self.client.get(reverse("equipamentos"), {"status": Ativo.Status.LOCADO})

        self.assertContains(response, "LOC-0001")
        self.assertContains(response, "Cliente Obra")
