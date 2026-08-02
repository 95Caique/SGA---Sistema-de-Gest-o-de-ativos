from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import EmpresaConfig


class EmpresaConfigTests(TestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@loca360.local",
            password="senha-forte",
        )

    def test_configuracoes_empresa_exige_superuser(self):
        response = self.client.get(reverse("configuracoes_empresa"))

        self.assertRedirects(response, reverse("dashboard"))

    def test_tela_configuracoes_cria_configuracao_padrao(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("configuracoes_empresa"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configuracoes da empresa")
        self.assertEqual(EmpresaConfig.objects.count(), 1)

    def test_atualiza_dados_da_empresa(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("configuracoes_empresa"),
            data={
                "nome_fantasia": "Estoque Now",
                "razao_social": "Estoque Now LTDA",
                "documento": "12.345.678/0001-90",
                "email": "contato@estoquenow.com.br",
                "telefone": "(62) 3000-0000",
                "whatsapp": "5562999999999",
                "endereco": "Rua 1, 100 - Goiania/GO",
            },
        )

        empresa = EmpresaConfig.atual()
        self.assertRedirects(response, reverse("configuracoes_empresa"))
        self.assertEqual(empresa.nome_fantasia, "Estoque Now")
        self.assertEqual(empresa.razao_social, "Estoque Now LTDA")
        self.assertEqual(empresa.whatsapp, "5562999999999")

    def test_layout_exibe_empresa_configurada(self):
        EmpresaConfig.objects.create(
            pk=1,
            nome_fantasia="Estoque Now",
            razao_social="Estoque Now LTDA",
            documento="12.345.678/0001-90",
            email="contato@estoquenow.com.br",
        )

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Estoque Now LTDA")
        self.assertContains(response, "contato@estoquenow.com.br")

    def test_menu_configuracoes_aparece_apenas_para_superuser(self):
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, reverse("configuracoes_empresa"))

        self.client.force_login(self.superuser)
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, reverse("configuracoes_empresa"))
