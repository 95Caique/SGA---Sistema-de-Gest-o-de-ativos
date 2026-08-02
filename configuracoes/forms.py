from django import forms

from .models import EmpresaConfig


class EmpresaConfigForm(forms.ModelForm):
    class Meta:
        model = EmpresaConfig
        fields = [
            "nome_fantasia",
            "razao_social",
            "documento",
            "email",
            "telefone",
            "whatsapp",
            "endereco",
        ]
        widgets = {
            "endereco": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            "nome_fantasia": "Ex: Estoque Now",
            "razao_social": "Ex: Estoque Now LTDA",
            "documento": "Ex: 00.000.000/0001-00",
            "email": "Ex: contato@estoquenow.com.br",
            "telefone": "Ex: (62) 3000-0000",
            "whatsapp": "Ex: 5562999999999",
            "endereco": "Ex: Rua, numero, bairro - Cidade/UF",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            field.widget.attrs.update({"placeholder": placeholders[field_name]})
