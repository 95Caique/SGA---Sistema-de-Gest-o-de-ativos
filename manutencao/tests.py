from django.test import TestCase
from django.urls import reverse

from ativos.models import Ativo, CategoriaAtivo

from .forms import OrdemManutencaoForm
from .models import OrdemManutencao


class ManutencaoOperacaoTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaAtivo.objects.create(nome="Construcao")
        self.ativo = Ativo.objects.create(
            codigo="BET-001",
            nome="Betoneira 400L",
            categoria=self.categoria,
            status=Ativo.Status.DISPONIVEL,
        )

    def test_cria_ordem_e_coloca_ativo_em_manutencao(self):
        response = self.client.post(
            reverse("manutencao_create"),
            data={
                "codigo": "MAN-0001",
                "ativo": self.ativo.pk,
                "tipo": OrdemManutencao.Tipo.CORRETIVA,
                "prioridade": OrdemManutencao.Prioridade.ALTA,
                "data_prevista": "2026-07-15",
                "responsavel": "Tecnico",
                "descricao": "Troca de rolamento",
                "custo_estimado": "250.00",
            },
        )

        self.ativo.refresh_from_db()
        ordem = OrdemManutencao.objects.get(codigo="MAN-0001")
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(ordem.ativo, self.ativo)
        self.assertEqual(self.ativo.status, Ativo.Status.MANUTENCAO)

    def test_finaliza_ordem_e_libera_ativo(self):
        ordem = OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo",
        )
        ordem.colocar_ativo_em_manutencao()

        response = self.client.post(reverse("manutencao_finalizar", kwargs={"pk": ordem.pk}))

        self.ativo.refresh_from_db()
        ordem.refresh_from_db()
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(ordem.status, OrdemManutencao.Status.FINALIZADA)
        self.assertEqual(self.ativo.status, Ativo.Status.DISPONIVEL)
        self.assertIsNotNone(ordem.data_conclusao)

    def test_form_lista_apenas_ativos_disponiveis(self):
        ativo_locado = Ativo.objects.create(
            codigo="BET-002",
            nome="Betoneira locada",
            categoria=self.categoria,
            status=Ativo.Status.LOCADO,
        )

        form = OrdemManutencaoForm()

        self.assertIn(self.ativo, form.fields["ativo"].queryset)
        self.assertNotIn(ativo_locado, form.fields["ativo"].queryset)
