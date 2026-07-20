from datetime import date

from django.db import models


class OrdemManutencao(models.Model):
    class Tipo(models.TextChoices):
        PREVENTIVA = "preventiva", "Preventiva"
        CORRETIVA = "corretiva", "Corretiva"

    class Status(models.TextChoices):
        ABERTA = "aberta", "Aberta"
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        FINALIZADA = "finalizada", "Finalizada"
        CANCELADA = "cancelada", "Cancelada"

    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"

    codigo = models.CharField(max_length=30, unique=True)
    ativo = models.ForeignKey("ativos.Ativo", on_delete=models.PROTECT, related_name="ordens_manutencao")
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.CORRETIVA)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTA)
    prioridade = models.CharField(max_length=20, choices=Prioridade.choices, default=Prioridade.MEDIA)
    data_abertura = models.DateField(auto_now_add=True)
    data_prevista = models.DateField(null=True, blank=True)
    data_conclusao = models.DateField(null=True, blank=True)
    responsavel = models.CharField(max_length=120, blank=True)
    descricao = models.TextField()
    solucao = models.TextField(blank=True)
    custo_estimado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custo_real = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-data_abertura", "codigo"]
        verbose_name = "ordem de manutencao"
        verbose_name_plural = "ordens de manutencao"

    def __str__(self):
        return f"{self.codigo} - {self.ativo.codigo}"

    def colocar_ativo_em_manutencao(self):
        from ativos.models import Ativo

        if self.status in [self.Status.ABERTA, self.Status.EM_ANDAMENTO]:
            self.ativo.status = Ativo.Status.MANUTENCAO
            self.ativo.save(update_fields=["status", "atualizado_em"])

    def iniciar(self):
        self.status = self.Status.EM_ANDAMENTO
        self.save(update_fields=["status", "atualizado_em"])
        self.colocar_ativo_em_manutencao()

    def finalizar(self):
        from ativos.models import Ativo

        self.status = self.Status.FINALIZADA
        self.data_conclusao = date.today()
        self.save(update_fields=["status", "data_conclusao", "atualizado_em"])
        self.ativo.status = Ativo.Status.DISPONIVEL
        self.ativo.save(update_fields=["status", "atualizado_em"])

    def cancelar(self):
        from ativos.models import Ativo

        self.status = self.Status.CANCELADA
        self.data_conclusao = date.today()
        self.save(update_fields=["status", "data_conclusao", "atualizado_em"])
        self.ativo.status = Ativo.Status.DISPONIVEL
        self.ativo.save(update_fields=["status", "atualizado_em"])
