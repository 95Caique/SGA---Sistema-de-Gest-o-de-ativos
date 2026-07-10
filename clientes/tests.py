from django.test import TestCase
from django.urls import reverse

from .models import Cliente, EnderecoCliente


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
