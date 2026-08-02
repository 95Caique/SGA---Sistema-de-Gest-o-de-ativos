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

    def test_cria_ordem_com_custo_estimado_em_formato_brasileiro(self):
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
                "custo_estimado": "400,00",
            },
        )

        ordem = OrdemManutencao.objects.get(codigo="MAN-0001")
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(str(ordem.custo_estimado), "400.00")

    def test_cria_ordem_com_custo_estimado_sem_centavos(self):
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
                "custo_estimado": "400",
            },
        )

        ordem = OrdemManutencao.objects.get(codigo="MAN-0001")
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(str(ordem.custo_estimado), "400.00")

    def test_finaliza_ordem_e_libera_ativo(self):
        ordem = OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo",
        )
        ordem.colocar_ativo_em_manutencao()

        response = self.client.post(
            reverse("manutencao_finalizar", kwargs={"pk": ordem.pk}),
            data={
                "solucao": "Rolamento substituido",
                "custo_real": "275,50",
            },
        )

        self.ativo.refresh_from_db()
        ordem.refresh_from_db()
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(ordem.status, OrdemManutencao.Status.FINALIZADA)
        self.assertEqual(self.ativo.status, Ativo.Status.DISPONIVEL)
        self.assertIsNotNone(ordem.data_conclusao)
        self.assertEqual(ordem.solucao, "Rolamento substituido")
        self.assertEqual(str(ordem.custo_real), "275.50")

    def test_tela_de_conclusao_exibe_formulario(self):
        ordem = OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo",
            custo_estimado="250.00",
        )

        response = self.client.get(reverse("manutencao_finalizar", kwargs={"pk": ordem.pk}))

        self.assertContains(response, "Finalizar manutencao MAN-0001")
        self.assertContains(response, "Solucao aplicada")
        self.assertContains(response, "Custo real")

    def test_nova_manutencao_exibe_detalhes_do_equipamento(self):
        self.ativo.localizacao_atual = "Deposito matriz"
        self.ativo.horimetro_atual = "120.5"
        self.ativo.proxima_manutencao_horas = "200.0"
        self.ativo.permite_rastreamento = True
        self.ativo.save()

        response = self.client.get(reverse("manutencao_create"))

        self.assertContains(response, "Detalhes do equipamento")
        self.assertContains(response, "BET-001")
        self.assertContains(response, "Betoneira 400L")
        self.assertContains(response, "Deposito matriz")
        self.assertContains(response, "120,5")
        self.assertContains(response, "Sim")

    def test_lista_formata_custos_com_moeda(self):
        OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            status=OrdemManutencao.Status.FINALIZADA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo",
            solucao="Troca feita",
            custo_estimado="250.00",
            custo_real="275.50",
        )

        response = self.client.get(reverse("manutencao"))

        self.assertContains(response, "R$ 250,00")
        self.assertContains(response, "Real R$ 275,50")

    def test_cancela_ordem_e_libera_ativo(self):
        ordem = OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo cancelado",
        )
        ordem.colocar_ativo_em_manutencao()

        response = self.client.post(reverse("manutencao_cancelar", kwargs={"pk": ordem.pk}))

        self.ativo.refresh_from_db()
        ordem.refresh_from_db()
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(ordem.status, OrdemManutencao.Status.CANCELADA)
        self.assertEqual(self.ativo.status, Ativo.Status.DISPONIVEL)
        self.assertIsNotNone(ordem.data_conclusao)

    def test_inicia_ordem_aberta(self):
        ordem = OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo",
        )

        response = self.client.post(reverse("manutencao_iniciar", kwargs={"pk": ordem.pk}))

        self.ativo.refresh_from_db()
        ordem.refresh_from_db()
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(ordem.status, OrdemManutencao.Status.EM_ANDAMENTO)
        self.assertEqual(self.ativo.status, Ativo.Status.MANUTENCAO)

    def test_iniciar_bloqueia_ordem_finalizada(self):
        ordem = OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            status=OrdemManutencao.Status.FINALIZADA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo",
        )

        response = self.client.post(reverse("manutencao_iniciar", kwargs={"pk": ordem.pk}))

        ordem.refresh_from_db()
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(ordem.status, OrdemManutencao.Status.FINALIZADA)

    def test_cancelar_bloqueia_ordem_finalizada(self):
        ordem = OrdemManutencao.objects.create(
            codigo="MAN-0001",
            ativo=self.ativo,
            tipo=OrdemManutencao.Tipo.CORRETIVA,
            status=OrdemManutencao.Status.FINALIZADA,
            prioridade=OrdemManutencao.Prioridade.MEDIA,
            descricao="Reparo",
        )

        response = self.client.post(reverse("manutencao_cancelar", kwargs={"pk": ordem.pk}))

        ordem.refresh_from_db()
        self.assertRedirects(response, reverse("manutencao"))
        self.assertEqual(ordem.status, OrdemManutencao.Status.FINALIZADA)

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
