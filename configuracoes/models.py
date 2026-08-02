from django.db import models


class EmpresaConfig(models.Model):
    nome_fantasia = models.CharField(max_length=120, default="Loca360")
    razao_social = models.CharField(max_length=160, default="Locadora Alpha LTDA")
    documento = models.CharField(max_length=30, default="00.000.000/0001-00")
    email = models.EmailField(default="contato@loca360.local")
    telefone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    endereco = models.CharField(max_length=220, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "configuracao da empresa"
        verbose_name_plural = "configuracoes da empresa"

    def __str__(self):
        return self.nome_fantasia

    @classmethod
    def atual(cls):
        config, _created = cls.objects.get_or_create(pk=1)
        return config
