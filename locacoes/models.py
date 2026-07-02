from django.db import models
from django.db.models import Sum


class Locacao(models.Model):
    class Status(models.TextChoices):
        ORCAMENTO = "orcamento", "Orcamento"
        AGENDADA = "agendada", "Agendada"
        ATIVA = "ativa", "Ativa"
        FINALIZADA = "finalizada", "Finalizada"
        CANCELADA = "cancelada", "Cancelada"

    codigo = models.CharField(max_length=30, unique=True)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT, related_name="locacoes")
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORCAMENTO)
    endereco_entrega = models.ForeignKey(
        "clientes.EnderecoCliente",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="locacoes_entrega",
    )
    valor_equipamentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_servicos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_inicio", "codigo"]
        verbose_name = "locacao"
        verbose_name_plural = "locacoes"

    def __str__(self):
        return f"{self.codigo} - {self.cliente}"

    def recalcular_totais(self, salvar=True):
        total_itens = self.itens.aggregate(total=Sum("valor_total"))["total"] or 0
        self.valor_equipamentos = total_itens
        self.valor_total = self.valor_equipamentos + self.valor_servicos - self.valor_desconto

        if salvar:
            self.save(update_fields=["valor_equipamentos", "valor_total", "atualizado_em"])

    def sincronizar_status_ativos(self):
        if self.status != self.Status.ATIVA:
            return

        from ativos.models import Ativo

        ativos = Ativo.objects.filter(itens_locacao__locacao=self).exclude(status=Ativo.Status.MANUTENCAO)
        ativos.update(status=Ativo.Status.LOCADO)


class ItemLocacao(models.Model):
    locacao = models.ForeignKey(Locacao, on_delete=models.CASCADE, related_name="itens")
    ativo = models.ForeignKey("ativos.Ativo", on_delete=models.PROTECT, related_name="itens_locacao")
    quantidade = models.PositiveIntegerField(default=1)
    valor_diaria = models.DecimalField(max_digits=12, decimal_places=2)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    observacoes = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ["locacao__codigo", "ativo__codigo"]
        verbose_name = "item de locacao"
        verbose_name_plural = "itens de locacao"
        constraints = [
            models.UniqueConstraint(fields=["locacao", "ativo"], name="item_locacao_ativo_unico"),
        ]

    def __str__(self):
        return f"{self.locacao.codigo} - {self.ativo.codigo}"
