from django import forms

from .models import Ativo, CategoriaAtivo


class AtivoForm(forms.ModelForm):
    nova_categoria = forms.CharField(
        label="Nova categoria",
        max_length=100,
        required=False,
        help_text="Preencha somente se a categoria ainda nao existir.",
    )

    class Meta:
        model = Ativo
        fields = [
            "codigo",
            "patrimonio",
            "nome",
            "categoria",
            "nova_categoria",
            "status",
            "localizacao_atual",
            "permite_rastreamento",
            "horimetro_atual",
            "proxima_manutencao_horas",
            "observacoes",
        ]
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].required = False
        self.fields["categoria"].queryset = CategoriaAtivo.objects.filter(ativa=True)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "form-checkbox"})
            else:
                field.widget.attrs.update({"class": "form-control"})

            if field_name in {"codigo", "patrimonio"}:
                field.widget.attrs.update({"placeholder": "Ex: BET-034"})
            elif field_name == "nome":
                field.widget.attrs.update({"placeholder": "Ex: Betoneira Menegotti 400L"})
            elif field_name == "nova_categoria":
                field.widget.attrs.update({"placeholder": "Ex: Construcao"})
            elif field_name == "localizacao_atual":
                field.widget.attrs.update({"placeholder": "Ex: Deposito matriz"})

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get("categoria")
        nova_categoria = cleaned_data.get("nova_categoria")

        if not categoria and not nova_categoria:
            raise forms.ValidationError("Selecione uma categoria existente ou informe uma nova categoria.")

        return cleaned_data

    def save(self, commit=True):
        ativo = super().save(commit=False)
        nova_categoria = self.cleaned_data.get("nova_categoria")

        if nova_categoria and not self.cleaned_data.get("categoria"):
            categoria, _ = CategoriaAtivo.objects.get_or_create(nome=nova_categoria)
            ativo.categoria = categoria

        if commit:
            ativo.save()
            self.save_m2m()

        return ativo
