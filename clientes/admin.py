from django.contrib import admin

from .models import Cliente, ContatoCliente, EnderecoCliente


class EnderecoClienteInline(admin.TabularInline):
    model = EnderecoCliente
    extra = 0


class ContatoClienteInline(admin.TabularInline):
    model = ContatoCliente
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "tipo_pessoa", "telefone", "responsavel", "status")
    list_filter = ("tipo_pessoa", "status")
    search_fields = ("nome", "documento", "email", "telefone", "responsavel")
    inlines = (EnderecoClienteInline, ContatoClienteInline)


@admin.register(EnderecoCliente)
class EnderecoClienteAdmin(admin.ModelAdmin):
    list_display = ("cliente", "nome", "cidade", "estado", "principal")
    list_filter = ("estado", "principal")
    search_fields = ("cliente__nome", "logradouro", "cidade", "cep")


@admin.register(ContatoCliente)
class ContatoClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cliente", "cargo", "telefone", "whatsapp", "principal")
    list_filter = ("principal",)
    search_fields = ("nome", "cliente__nome", "email", "telefone", "whatsapp")
