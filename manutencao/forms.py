from django import forms

from ativos.models import Ativo

from .models import OrdemManutencao


class OrdemManutencaoForm(forms.ModelForm):
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
