from django.test import TestCase
from django.urls import reverse

from .models import Cliente


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
