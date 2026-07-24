from django.test import TestCase
from django.urls import reverse

from .models import Cliente, ContatoCliente, EnderecoCliente


class ClienteViewTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12345678000190",
            email="contato@forte.com.br",
            telefone="11999990000",
        )

    def test_edita_cliente(self):
        response = self.client.post(
            reverse("cliente_update", kwargs={"pk": self.cliente.pk}),
            data={
                "nome": "Construtora Forte Atualizada",
                "tipo_pessoa": Cliente.TipoPessoa.JURIDICA,
                "documento": "12345678000190",
                "email": "novo@forte.com.br",
                "telefone": "11888880000",
                "responsavel": "Marina",
                "status": Cliente.Status.ATIVO,
                "observacoes": "Cliente recorrente",
            },
        )

        self.cliente.refresh_from_db()
        self.assertRedirects(response, reverse("clientes"))
        self.assertEqual(self.cliente.nome, "Construtora Forte Atualizada")
        self.assertEqual(self.cliente.email, "novo@forte.com.br")
        self.assertEqual(self.cliente.responsavel, "Marina")

    def test_lista_clientes_filtra_por_status(self):
        Cliente.objects.create(
            nome="Cliente Bloqueado",
            documento="98765432000199",
            status=Cliente.Status.BLOQUEADO,
        )

        response = self.client.get(reverse("clientes"), {"status": Cliente.Status.BLOQUEADO})

        self.assertContains(response, "Cliente Bloqueado")
        self.assertNotContains(response, "Construtora Forte")

    def test_cria_endereco_do_cliente(self):
        response = self.client.post(
            reverse("cliente_endereco_create", kwargs={"pk": self.cliente.pk}),
            data={
                "nome": "Obra centro",
                "cep": "01000-000",
                "logradouro": "Rua A",
                "numero": "100",
                "complemento": "",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "estado": "SP",
                "principal": "on",
            },
        )

        endereco = EnderecoCliente.objects.get(cliente=self.cliente)
        self.assertRedirects(response, reverse("cliente_update", kwargs={"pk": self.cliente.pk}))
        self.assertEqual(endereco.nome, "Obra centro")
        self.assertTrue(endereco.principal)

    def test_endpoint_enderecos_retorna_nome_do_endereco(self):
        endereco = EnderecoCliente.objects.create(
            cliente=self.cliente,
            nome="OD - Principal",
            logradouro="Rua A",
            numero="10",
            cidade="Goiania",
            estado="GO",
        )

        response = self.client.get(reverse("cliente_enderecos_options", kwargs={"pk": self.cliente.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["enderecos"],
            [{"id": endereco.pk, "label": "OD - Principal - Rua A, 10 - Goiania/GO"}],
        )

    def test_novo_endereco_principal_desmarca_anterior(self):
        endereco_antigo = EnderecoCliente.objects.create(
            cliente=self.cliente,
            nome="Antigo",
            logradouro="Rua B",
            cidade="Sao Paulo",
            estado="SP",
            principal=True,
        )

        self.client.post(
            reverse("cliente_endereco_create", kwargs={"pk": self.cliente.pk}),
            data={
                "nome": "Novo",
                "cep": "",
                "logradouro": "Rua C",
                "numero": "",
                "complemento": "",
                "bairro": "",
                "cidade": "Sao Paulo",
                "estado": "SP",
                "principal": "on",
            },
        )

        endereco_antigo.refresh_from_db()
        self.assertFalse(endereco_antigo.principal)

    def test_edicao_cliente_exibe_enderecos(self):
        EnderecoCliente.objects.create(
            cliente=self.cliente,
            nome="Obra centro",
            logradouro="Rua A",
            cidade="Sao Paulo",
            estado="SP",
            principal=True,
        )

        response = self.client.get(reverse("cliente_update", kwargs={"pk": self.cliente.pk}))

        self.assertContains(response, "Obra centro")
        self.assertContains(response, "Rua A")

    def test_edita_endereco_do_cliente(self):
        endereco = EnderecoCliente.objects.create(
            cliente=self.cliente,
            nome="Obra centro",
            logradouro="Rua A",
            cidade="Sao Paulo",
            estado="SP",
        )

        response = self.client.post(
            reverse("cliente_endereco_update", kwargs={"pk": self.cliente.pk, "endereco_pk": endereco.pk}),
            data={
                "nome": "Obra norte",
                "cep": "02000-000",
                "logradouro": "Rua Norte",
                "numero": "200",
                "complemento": "",
                "bairro": "Santana",
                "cidade": "Sao Paulo",
                "estado": "SP",
                "principal": "on",
            },
        )

        endereco.refresh_from_db()
        self.assertRedirects(response, reverse("cliente_update", kwargs={"pk": self.cliente.pk}))
        self.assertEqual(endereco.nome, "Obra norte")
        self.assertEqual(endereco.logradouro, "Rua Norte")
        self.assertTrue(endereco.principal)

    def test_cria_contato_do_cliente(self):
        response = self.client.post(
            reverse("cliente_contato_create", kwargs={"pk": self.cliente.pk}),
            data={
                "nome": "Marina",
                "cargo": "Compras",
                "email": "marina@forte.com.br",
                "telefone": "11999990000",
                "whatsapp": "11999990000",
                "principal": "on",
            },
        )

        contato = ContatoCliente.objects.get(cliente=self.cliente)
        self.assertRedirects(response, reverse("cliente_update", kwargs={"pk": self.cliente.pk}))
        self.assertEqual(contato.nome, "Marina")
        self.assertTrue(contato.principal)

    def test_edicao_cliente_exibe_contatos(self):
        ContatoCliente.objects.create(
            cliente=self.cliente,
            nome="Marina",
            cargo="Compras",
            email="marina@forte.com.br",
            principal=True,
        )

        response = self.client.get(reverse("cliente_update", kwargs={"pk": self.cliente.pk}))

        self.assertContains(response, "Marina")
        self.assertContains(response, "Compras")

    def test_edita_contato_do_cliente(self):
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome="Marina",
            cargo="Compras",
            email="marina@forte.com.br",
        )

        response = self.client.post(
            reverse("cliente_contato_update", kwargs={"pk": self.cliente.pk, "contato_pk": contato.pk}),
            data={
                "nome": "Marina Silva",
                "cargo": "Operacoes",
                "email": "marina.silva@forte.com.br",
                "telefone": "11888880000",
                "whatsapp": "11888880000",
                "principal": "on",
            },
        )

        contato.refresh_from_db()
        self.assertRedirects(response, reverse("cliente_update", kwargs={"pk": self.cliente.pk}))
        self.assertEqual(contato.nome, "Marina Silva")
        self.assertEqual(contato.cargo, "Operacoes")
        self.assertTrue(contato.principal)
