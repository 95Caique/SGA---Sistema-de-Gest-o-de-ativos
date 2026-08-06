from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Locacao(models.Model):
    class Status(models.TextChoices):
        ORCAMENTO = "orcamento", "Orcamento"
        AGENDADA = "agendada", "Agendada"
        ATIVA = "ativa", "Ativa"
        FINALIZADA = "finalizada", "Finalizada"
        CANCELADA = "cancelada", "Cancelada"

    class StatusPagamento(models.TextChoices):
        ABERTO = "aberto", "Em aberto"
        RECEBIDO = "recebido", "Recebido"
        CANCELADO = "cancelado", "Cancelado"

    codigo = models.CharField(max_length=30, unique=True)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT, related_name="locacoes")
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORCAMENTO)
    status_pagamento = models.CharField(
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.ABERTO,
    )
    data_pagamento = models.DateField(null=True, blank=True)
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
        from rastreamento.models import PosicaoRastreamento, Rastreador

        ativos = Ativo.objects.filter(itens_locacao__locacao=self).exclude(status=Ativo.Status.MANUTENCAO)
        ativos.update(status=Ativo.Status.LOCADO)

        for ativo in ativos.filter(permite_rastreamento=True):
            rastreador, _created = Rastreador.objects.update_or_create(
                ativo=ativo,
                defaults={
                    "identificador": f"SIM-{ativo.codigo}",
                    "status": Rastreador.Status.ONLINE,
                    "usando_dados_simulados": True,
                },
            )
            if not rastreador.posicoes.exists():
                PosicaoRastreamento.objects.create(
                    rastreador=rastreador,
                    latitude=_coordenada_simulada(ativo.codigo, Decimal("-16.6869")),
                    longitude=_coordenada_simulada(ativo.codigo[::-1], Decimal("-49.2648")),
                    endereco_referencia=_referencia_entrega(self, ativo),
                    velocidade_kmh=Decimal("0.0"),
                    registrada_em=timezone.now(),
                )

    def finalizar_operacao(self):
        from ativos.models import Ativo
        from rastreamento.models import Rastreador

        ativos = Ativo.objects.filter(itens_locacao__locacao=self).exclude(status=Ativo.Status.MANUTENCAO)
        ativos.update(status=Ativo.Status.DISPONIVEL)
        Rastreador.objects.filter(ativo__in=ativos, usando_dados_simulados=True).update(status=Rastreador.Status.OFFLINE)

    def marcar_recebida(self, data_pagamento):
        self.status_pagamento = self.StatusPagamento.RECEBIDO
        self.data_pagamento = data_pagamento
        self.save(update_fields=["status_pagamento", "data_pagamento", "atualizado_em"])

    def reabrir_pagamento(self):
        self.status_pagamento = self.StatusPagamento.ABERTO
        self.data_pagamento = None
        self.save(update_fields=["status_pagamento", "data_pagamento", "atualizado_em"])

    def cancelar_pagamento(self):
        self.status_pagamento = self.StatusPagamento.CANCELADO
        self.data_pagamento = None
        self.save(update_fields=["status_pagamento", "data_pagamento", "atualizado_em"])


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

    def clean(self):
        super().clean()

        if not self._state.adding or not self.ativo_id:
            return

        from ativos.models import Ativo

        if self.ativo.status != Ativo.Status.DISPONIVEL:
            raise ValidationError({"ativo": "Este ativo nao esta disponivel para locacao."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class HistoricoLocacao(models.Model):
    class Tipo(models.TextChoices):
        CRIACAO = "criacao", "Criacao"
        EDICAO = "edicao", "Edicao"
        ITEM_ADICIONADO = "item_adicionado", "Item adicionado"
        ITEM_REMOVIDO = "item_removido", "Item removido"
        APROVACAO = "aprovacao", "Aprovacao"
        ATIVACAO = "ativacao", "Ativacao"
        CANCELAMENTO = "cancelamento", "Cancelamento"
        FINALIZACAO = "finalizacao", "Finalizacao"

    locacao = models.ForeignKey(Locacao, on_delete=models.CASCADE, related_name="historicos")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    descricao = models.CharField(max_length=255)
    usuario_nome = models.CharField(max_length=150, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "historico de locacao"
        verbose_name_plural = "historicos de locacao"

    def __str__(self):
        return f"{self.locacao.codigo} - {self.get_tipo_display()}"


def _coordenada_simulada(texto, base):
    deslocamento = Decimal(sum(ord(char) for char in texto) % 90) / Decimal("10000")
    return base + deslocamento


def _referencia_entrega(locacao, ativo):
    if locacao.endereco_entrega:
        return str(locacao.endereco_entrega)

    if ativo.localizacao_atual:
        return ativo.localizacao_atual

    return f"Posicao simulada da locacao {locacao.codigo}"
