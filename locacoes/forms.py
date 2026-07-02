from django import forms

from .models import Locacao


class LocacaoForm(forms.ModelForm):
    class Meta:
        model = Locacao
        fields = [
            "codigo",
            "cliente",
            "data_inicio",
            "data_fim",
            "status",
            "endereco_entrega",
            "valor_equipamentos",
            "valor_servicos",
            "valor_desconto",
            "valor_total",
            "observacoes",
        ]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["endereco_entrega"].required = False

        placeholders = {
            "codigo": "Ex: LOC-0001",
            "valor_equipamentos": "0,00",
            "valor_servicos": "0,00",
            "valor_desconto": "0,00",
            "valor_total": "0,00",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            if field_name in placeholders:
                field.widget.attrs.update({"placeholder": placeholders[field_name]})

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")

        if data_inicio and data_fim and data_fim < data_inicio:
            raise forms.ValidationError("A data final nao pode ser anterior a data inicial.")

        return cleaned_data
