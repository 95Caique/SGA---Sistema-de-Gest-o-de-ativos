from django.test import TestCase
from django.urls import reverse

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
