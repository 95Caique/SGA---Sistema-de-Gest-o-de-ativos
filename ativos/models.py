from django.db import models


class CategoriaAtivo(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "categoria de ativo"
        verbose_name_plural = "categorias de ativos"

    def __str__(self):
        return self.nome


class Ativo(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = "disponivel", "Disponivel"
        LOCADO = "locado", "Locado"
        MANUTENCAO = "manutencao", "Manutencao"
        INATIVO = "inativo", "Inativo"

    codigo = models.CharField(max_length=30, unique=True)
    patrimonio = models.CharField(max_length=50, blank=True)
    nome = models.CharField(max_length=160)
    categoria = models.ForeignKey(CategoriaAtivo, on_delete=models.PROTECT, related_name="ativos")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISPONIVEL)
    localizacao_atual = models.CharField(max_length=180, blank=True)
    permite_rastreamento = models.BooleanField(default=False)
    horimetro_atual = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    proxima_manutencao_horas = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "ativo"
        verbose_name_plural = "ativos"

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
