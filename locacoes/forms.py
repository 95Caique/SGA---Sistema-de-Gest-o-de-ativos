from django import forms

from ativos.models import Ativo

from .models import ItemLocacao, Locacao


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


class ItemLocacaoForm(forms.ModelForm):
    class Meta:
        model = ItemLocacao
        fields = [
            "ativo",
            "quantidade",
            "valor_diaria",
            "valor_total",
            "observacoes",
        ]
        widgets = {
            "observacoes": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ativo"].queryset = Ativo.objects.filter(status=Ativo.Status.DISPONIVEL)
        placeholders = {
            "valor_diaria": "0,00",
            "valor_total": "0,00",
            "observacoes": "Observacao opcional",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            if field_name in placeholders:
                field.widget.attrs.update({"placeholder": placeholders[field_name]})

    def clean_ativo(self):
        ativo = self.cleaned_data["ativo"]

        if ativo.status != Ativo.Status.DISPONIVEL:
            raise forms.ValidationError("Este ativo nao esta disponivel para locacao.")

        return ativo
