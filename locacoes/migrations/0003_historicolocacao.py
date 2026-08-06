import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("locacoes", "0002_locacao_data_pagamento_locacao_status_pagamento"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricoLocacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("criacao", "Criacao"),
                            ("edicao", "Edicao"),
                            ("item_adicionado", "Item adicionado"),
                            ("item_removido", "Item removido"),
                            ("aprovacao", "Aprovacao"),
                            ("ativacao", "Ativacao"),
                            ("cancelamento", "Cancelamento"),
                            ("finalizacao", "Finalizacao"),
                        ],
                        max_length=30,
                    ),
                ),
                ("descricao", models.CharField(max_length=255)),
                ("usuario_nome", models.CharField(blank=True, max_length=150)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "locacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historicos",
                        to="locacoes.locacao",
                    ),
                ),
            ],
            options={
                "verbose_name": "historico de locacao",
                "verbose_name_plural": "historicos de locacao",
                "ordering": ["-criado_em", "-id"],
            },
        ),
    ]
