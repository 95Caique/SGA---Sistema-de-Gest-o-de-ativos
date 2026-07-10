from django import forms

from ativos.models import Ativo
from clientes.models import Cliente, EnderecoCliente

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
        self.fields["cliente"].queryset = Cliente.objects.filter(status=Cliente.Status.ATIVO)
        self.fields["endereco_entrega"].required = False
        self.fields["status"].choices = [
            (Locacao.Status.ORCAMENTO, Locacao.Status.ORCAMENTO.label),
            (Locacao.Status.AGENDADA, Locacao.Status.AGENDADA.label),
        ]

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

        cliente_id = self.data.get("cliente") if self.is_bound else self.instance.cliente_id
        self.fields["endereco_entrega"].queryset = EnderecoCliente.objects.none()

        if cliente_id:
            self.fields["endereco_entrega"].queryset = EnderecoCliente.objects.filter(cliente_id=cliente_id)

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get("cliente")
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")
        endereco_entrega = cleaned_data.get("endereco_entrega")

        if data_inicio and data_fim and data_fim < data_inicio:
            raise forms.ValidationError("A data final nao pode ser anterior a data inicial.")

        if cliente and endereco_entrega and endereco_entrega.cliente_id != cliente.id:
            self.add_error("endereco_entrega", "Selecione um endereco vinculado ao cliente da locacao.")

        return cleaned_data

    def clean_status(self):
        status = self.cleaned_data.get("status")

        if status not in [Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA]:
            raise forms.ValidationError("Nova locacao deve iniciar como orcamento ou agendada.")

        return status

    def clean_cliente(self):
        cliente = self.cleaned_data.get("cliente")

        if cliente and cliente.status != Cliente.Status.ATIVO:
            raise forms.ValidationError("Somente clientes ativos podem gerar locacao.")

        return cliente


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
        self.fields["valor_total"].required = False
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
        ativo = self.cleaned_data.get("ativo")

        if not ativo:
            return ativo

        if ativo.status != Ativo.Status.DISPONIVEL:
            raise forms.ValidationError("Este ativo nao esta disponivel para locacao.")

        return ativo

    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get("quantidade")
        valor_diaria = cleaned_data.get("valor_diaria")
        valor_total = cleaned_data.get("valor_total")

        if quantidade and valor_diaria and not valor_total:
            cleaned_data["valor_total"] = quantidade * valor_diaria

        return cleaned_data
