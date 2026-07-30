from django import forms

from ativos.models import Ativo

from .models import OrdemManutencao


class MoneyBRField(forms.DecimalField):
    widget = forms.TextInput

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace("R$", "").replace(" ", "")

            if "," in value:
                value = value.replace(".", "").replace(",", ".")

        return super().to_python(value)


class OrdemManutencaoForm(forms.ModelForm):
    custo_estimado = MoneyBRField(max_digits=12, decimal_places=2)

    class Meta:
        model = OrdemManutencao
        fields = [
            "codigo",
            "ativo",
            "tipo",
            "prioridade",
            "data_prevista",
            "responsavel",
            "descricao",
            "custo_estimado",
        ]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
            "descricao": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ativo"].queryset = Ativo.objects.filter(status=Ativo.Status.DISPONIVEL)

        placeholders = {
            "codigo": "Ex: MAN-0001",
            "responsavel": "Tecnico responsavel",
            "custo_estimado": "0,00",
            "descricao": "Descreva o problema ou servico preventivo",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            if field_name in placeholders:
                field.widget.attrs.update({"placeholder": placeholders[field_name]})

        self.fields["custo_estimado"].widget.attrs.update({"data-money-field": "true", "inputmode": "decimal"})


class ConclusaoManutencaoForm(forms.ModelForm):
    custo_real = MoneyBRField(max_digits=12, decimal_places=2)

    class Meta:
        model = OrdemManutencao
        fields = ["solucao", "custo_real"]
        widgets = {
            "solucao": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "solucao": "Solucao aplicada",
            "custo_real": "Custo real",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "solucao": "Descreva o servico realizado",
            "custo_real": "0,00",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
            if field_name in placeholders:
                field.widget.attrs.update({"placeholder": placeholders[field_name]})

        self.fields["custo_real"].widget.attrs.update({"data-money-field": "true", "inputmode": "decimal"})
