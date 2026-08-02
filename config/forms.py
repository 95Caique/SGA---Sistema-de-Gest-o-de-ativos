from django import forms


class MoneyBRField(forms.DecimalField):
    widget = forms.TextInput

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace("R$", "").replace(" ", "")

            if "," in value:
                value = value.replace(".", "").replace(",", ".")

        return super().to_python(value)


def setup_money_field(field):
    field.widget.attrs.update(
        {
            "data-money-field": "true",
            "inputmode": "decimal",
        }
    )
