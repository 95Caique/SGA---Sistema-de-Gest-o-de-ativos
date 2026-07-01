from django.db import models


class Rastreador(models.Model):
    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        SEM_COMUNICACAO = "sem_comunicacao", "Sem comunicacao"
        MANUTENCAO = "manutencao", "Manutencao"

    ativo = models.OneToOneField("ativos.Ativo", on_delete=models.CASCADE, related_name="rastreador")
    identificador = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONLINE)
    bateria_percentual = models.PositiveSmallIntegerField(default=100)
    sinal_gsm_percentual = models.PositiveSmallIntegerField(default=100)
    usando_dados_simulados = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ativo__codigo"]
        verbose_name = "rastreador"
        verbose_name_plural = "rastreadores"

    def __str__(self):
        return f"{self.identificador} - {self.ativo.codigo}"


class PosicaoRastreamento(models.Model):
    rastreador = models.ForeignKey(Rastreador, on_delete=models.CASCADE, related_name="posicoes")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    endereco_referencia = models.CharField(max_length=180, blank=True)
    velocidade_kmh = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    registrada_em = models.DateTimeField()
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-registrada_em"]
        verbose_name = "posicao de rastreamento"
        verbose_name_plural = "posicoes de rastreamento"

    def __str__(self):
        return f"{self.rastreador.identificador} em {self.registrada_em:%d/%m/%Y %H:%M}"
