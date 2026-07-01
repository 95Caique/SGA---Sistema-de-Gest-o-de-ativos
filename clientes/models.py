from django.db import models


class Cliente(models.Model):
    class TipoPessoa(models.TextChoices):
        FISICA = "fisica", "Pessoa fisica"
        JURIDICA = "juridica", "Pessoa juridica"

    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        INATIVO = "inativo", "Inativo"
        BLOQUEADO = "bloqueado", "Bloqueado"

    nome = models.CharField(max_length=160)
    tipo_pessoa = models.CharField(max_length=20, choices=TipoPessoa.choices, default=TipoPessoa.JURIDICA)
    documento = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    responsavel = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ATIVO)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    def __str__(self):
        return self.nome


class EnderecoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="enderecos")
    nome = models.CharField(max_length=80, default="Principal")
    cep = models.CharField(max_length=9, blank=True)
    logradouro = models.CharField(max_length=160)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=80, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    principal = models.BooleanField(default=True)

    class Meta:
        ordering = ["cliente__nome", "-principal", "nome"]
        verbose_name = "endereco de cliente"
        verbose_name_plural = "enderecos de clientes"

    def __str__(self):
        return f"{self.cliente} - {self.cidade}/{self.estado}"


class ContatoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="contatos")
    nome = models.CharField(max_length=120)
    cargo = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    principal = models.BooleanField(default=False)

    class Meta:
        ordering = ["cliente__nome", "-principal", "nome"]
        verbose_name = "contato de cliente"
        verbose_name_plural = "contatos de clientes"

    def __str__(self):
        return f"{self.nome} - {self.cliente}"
