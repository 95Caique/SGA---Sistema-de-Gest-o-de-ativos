from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from ativos.models import Ativo, CategoriaAtivo
from clientes.models import Cliente, EnderecoCliente
from rastreamento.models import Rastreador

from .forms import ItemLocacaoForm, LocacaoForm
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

    def test_form_item_locacao_lista_apenas_ativos_disponiveis(self):
        ativo_locado = Ativo.objects.create(
            codigo="BET-002",
            nome="Betoneira locada",
            categoria=self.categoria,
            status=Ativo.Status.LOCADO,
        )

        form = ItemLocacaoForm()

        self.assertIn(self.ativo, form.fields["ativo"].queryset)
        self.assertNotIn(ativo_locado, form.fields["ativo"].queryset)

    def test_form_item_locacao_rejeita_ativo_indisponivel(self):
        self.ativo.status = Ativo.Status.LOCADO
        self.ativo.save()

        form = ItemLocacaoForm(
            data={
                "ativo": self.ativo.pk,
                "quantidade": 1,
                "valor_diaria": "100.00",
                "valor_total": "400.00",
                "observacoes": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("ativo", form.errors)

    def test_form_item_locacao_calcula_total_quando_nao_informado(self):
        form = ItemLocacaoForm(
            data={
                "ativo": self.ativo.pk,
                "quantidade": 3,
                "valor_diaria": "125.50",
                "valor_total": "",
                "observacoes": "",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["valor_total"], Decimal("376.50"))

    def test_model_item_locacao_rejeita_ativo_indisponivel(self):
        self.ativo.status = Ativo.Status.LOCADO
        self.ativo.save()

        with self.assertRaises(ValidationError):
            ItemLocacao.objects.create(
                locacao=self.locacao,
                ativo=self.ativo,
                quantidade=1,
                valor_diaria=Decimal("100.00"),
                valor_total=Decimal("400.00"),
            )

    def test_ativacao_rejeita_locacao_com_ativo_indisponivel(self):
        ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("400.00"),
        )
        self.ativo.status = Ativo.Status.LOCADO
        self.ativo.save()

        response = self.client.post(reverse("locacao_ativar", kwargs={"pk": self.locacao.pk}))

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertEqual(self.locacao.status, Locacao.Status.ORCAMENTO)

    def test_remove_item_da_locacao_e_recalcula_totais(self):
        item = ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("400.00"),
        )
        self.locacao.recalcular_totais()

        response = self.client.post(
            reverse("locacao_item_remove", kwargs={"pk": self.locacao.pk, "item_pk": item.pk})
        )

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertFalse(ItemLocacao.objects.filter(pk=item.pk).exists())
        self.assertEqual(self.locacao.valor_equipamentos, Decimal("0.00"))
        self.assertEqual(self.locacao.valor_total, Decimal("40.00"))

    def test_remove_item_bloqueia_locacao_ativa(self):
        item = ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("400.00"),
        )
        self.locacao.status = Locacao.Status.ATIVA
        self.locacao.save()

        response = self.client.post(
            reverse("locacao_item_remove", kwargs={"pk": self.locacao.pk, "item_pk": item.pk})
        )

        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertTrue(ItemLocacao.objects.filter(pk=item.pk).exists())

    def test_form_locacao_nao_permite_criar_ativa(self):
        form = LocacaoForm(
            data={
                "codigo": "LOC-0002",
                "cliente": self.cliente.pk,
                "data_inicio": "2026-07-10",
                "data_fim": "2026-07-12",
                "status": Locacao.Status.ATIVA,
                "endereco_entrega": "",
                "valor_equipamentos": "0.00",
                "valor_servicos": "0.00",
                "valor_desconto": "0.00",
                "valor_total": "0.00",
                "observacoes": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)

    def test_form_locacao_lista_apenas_clientes_ativos(self):
        cliente_bloqueado = Cliente.objects.create(
            nome="Cliente Bloqueado",
            documento="98765432000199",
            status=Cliente.Status.BLOQUEADO,
        )

        form = LocacaoForm()

        self.assertIn(self.cliente, form.fields["cliente"].queryset)
        self.assertNotIn(cliente_bloqueado, form.fields["cliente"].queryset)

    def test_lista_locacoes_filtra_por_status(self):
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=date(2026, 7, 10),
            data_fim=date(2026, 7, 12),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("locacoes"), {"status": Locacao.Status.AGENDADA})

        self.assertContains(response, "LOC-0002")
        self.assertNotContains(response, "LOC-0001")

    def test_lista_orcamentos_exibe_apenas_locacoes_em_orcamento(self):
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=date(2026, 7, 10),
            data_fim=date(2026, 7, 12),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("orcamentos"))

        self.assertContains(response, "LOC-0001")
        self.assertNotContains(response, "LOC-0002")

    def test_aprova_orcamento_com_item(self):
        ItemLocacao.objects.create(
            locacao=self.locacao,
            ativo=self.ativo,
            quantidade=1,
            valor_diaria=Decimal("100.00"),
            valor_total=Decimal("400.00"),
        )

        response = self.client.post(reverse("orcamento_aprovar", kwargs={"pk": self.locacao.pk}))

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertEqual(self.locacao.status, Locacao.Status.AGENDADA)

    def test_aprovar_orcamento_bloqueia_sem_item(self):
        response = self.client.post(reverse("orcamento_aprovar", kwargs={"pk": self.locacao.pk}))

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertEqual(self.locacao.status, Locacao.Status.ORCAMENTO)

    @patch("wkhtmltopdf.views.render_pdf_from_template", return_value=b"%PDF-1.4")
    def test_gera_pdf_do_orcamento(self, _render_pdf):
        response = self.client.get(reverse("orcamento_pdf", kwargs={"pk": self.locacao.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertIn("orcamento-LOC-0001.pdf", response["Content-Disposition"])

    def test_pdf_de_orcamento_bloqueia_locacao_agendada(self):
        self.locacao.status = Locacao.Status.AGENDADA
        self.locacao.save()

        response = self.client.get(reverse("orcamento_pdf", kwargs={"pk": self.locacao.pk}))

        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))

    def test_cancela_orcamento(self):
        response = self.client.post(reverse("locacao_cancelar", kwargs={"pk": self.locacao.pk}))

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertEqual(self.locacao.status, Locacao.Status.CANCELADA)

    def test_cancela_locacao_agendada(self):
        self.locacao.status = Locacao.Status.AGENDADA
        self.locacao.save()

        response = self.client.post(reverse("locacao_cancelar", kwargs={"pk": self.locacao.pk}))

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertEqual(self.locacao.status, Locacao.Status.CANCELADA)

    def test_cancelar_bloqueia_locacao_ativa(self):
        self.locacao.status = Locacao.Status.ATIVA
        self.locacao.save()

        response = self.client.post(reverse("locacao_cancelar", kwargs={"pk": self.locacao.pk}))

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertEqual(self.locacao.status, Locacao.Status.ATIVA)

    def test_edita_locacao_em_orcamento(self):
        response = self.client.post(
            reverse("locacao_update", kwargs={"pk": self.locacao.pk}),
            data={
                "codigo": "LOC-0001",
                "cliente": self.cliente.pk,
                "data_inicio": "2026-07-02",
                "data_fim": "2026-07-06",
                "status": Locacao.Status.AGENDADA,
                "endereco_entrega": "",
                "valor_equipamentos": "0.00",
                "valor_servicos": "80.00",
                "valor_desconto": "5.00",
                "valor_total": "75.00",
                "observacoes": "Entrega pela manha",
            },
        )

        self.locacao.refresh_from_db()
        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))
        self.assertEqual(self.locacao.status, Locacao.Status.AGENDADA)
        self.assertEqual(self.locacao.valor_servicos, Decimal("80.00"))
        self.assertEqual(self.locacao.observacoes, "Entrega pela manha")

    def test_edicao_bloqueia_locacao_ativa(self):
        self.locacao.status = Locacao.Status.ATIVA
        self.locacao.save()

        response = self.client.get(reverse("locacao_update", kwargs={"pk": self.locacao.pk}))

        self.assertRedirects(response, reverse("locacao_detail", kwargs={"pk": self.locacao.pk}))

    def test_form_locacao_filtra_enderecos_pelo_cliente(self):
        endereco_cliente = EnderecoCliente.objects.create(
            cliente=self.cliente,
            nome="Obra",
            logradouro="Rua A",
            cidade="Sao Paulo",
            estado="SP",
        )
        outro_cliente = Cliente.objects.create(nome="Outro Cliente", documento="98765432000199")
        endereco_outro_cliente = EnderecoCliente.objects.create(
            cliente=outro_cliente,
            nome="Matriz",
            logradouro="Rua B",
            cidade="Campinas",
            estado="SP",
        )

        form = LocacaoForm(data={"cliente": self.cliente.pk})

        self.assertIn(endereco_cliente, form.fields["endereco_entrega"].queryset)
        self.assertNotIn(endereco_outro_cliente, form.fields["endereco_entrega"].queryset)

    def test_form_locacao_rejeita_endereco_de_outro_cliente(self):
        outro_cliente = Cliente.objects.create(nome="Outro Cliente", documento="98765432000199")
        endereco_outro_cliente = EnderecoCliente.objects.create(
            cliente=outro_cliente,
            nome="Matriz",
            logradouro="Rua B",
            cidade="Campinas",
            estado="SP",
        )

        form = LocacaoForm(
            data={
                "codigo": "LOC-0002",
                "cliente": self.cliente.pk,
                "data_inicio": "2026-07-10",
                "data_fim": "2026-07-12",
                "status": Locacao.Status.ORCAMENTO,
                "endereco_entrega": endereco_outro_cliente.pk,
                "valor_equipamentos": "0.00",
                "valor_servicos": "0.00",
                "valor_desconto": "0.00",
                "valor_total": "0.00",
                "observacoes": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("endereco_entrega", form.errors)
