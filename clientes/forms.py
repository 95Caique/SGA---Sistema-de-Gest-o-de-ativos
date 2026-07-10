from django import forms

from .models import Cliente, EnderecoCliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome",
            "tipo_pessoa",
            "documento",
            "email",
            "telefone",
            "responsavel",
            "status",
            "observacoes",
        ]
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "nome": "Ex: Construtora Forte",
            "documento": "CPF ou CNPJ",
            "email": "contato@cliente.com.br",
            "telefone": "(00) 00000-0000",
            "responsavel": "Nome do responsavel",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            if field_name in placeholders:
                field.widget.attrs.update({"placeholder": placeholders[field_name]})


class EnderecoClienteForm(forms.ModelForm):
    class Meta:
        model = EnderecoCliente
        fields = [
            "nome",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "estado",
            "principal",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "nome": "Ex: Obra centro",
            "cep": "00000-000",
            "logradouro": "Rua, avenida ou estrada",
            "numero": "Numero",
            "complemento": "Complemento",
            "bairro": "Bairro",
            "cidade": "Cidade",
            "estado": "UF",
        }

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "form-checkbox"})
            else:
                field.widget.attrs.update({"class": "form-control"})

            if field_name in placeholders:
                field.widget.attrs.update({"placeholder": placeholders[field_name]})
