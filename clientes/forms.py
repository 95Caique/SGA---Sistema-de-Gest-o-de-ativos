from django import forms

from .models import Cliente


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
