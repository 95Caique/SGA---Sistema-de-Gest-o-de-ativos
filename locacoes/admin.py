from django.contrib import admin

from .models import HistoricoLocacao, ItemLocacao, Locacao


class ItemLocacaoInline(admin.TabularInline):
    model = ItemLocacao
    extra = 0
    autocomplete_fields = ("ativo",)


class HistoricoLocacaoInline(admin.TabularInline):
    model = HistoricoLocacao
    extra = 0
    fields = ("tipo", "descricao", "usuario_nome", "criado_em")
    readonly_fields = ("tipo", "descricao", "usuario_nome", "criado_em")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Locacao)
class LocacaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "cliente", "data_inicio", "data_fim", "status", "status_pagamento", "valor_total")
    list_filter = ("status", "status_pagamento", "data_inicio", "data_fim")
    search_fields = ("codigo", "cliente__nome", "cliente__documento")
    autocomplete_fields = ("cliente", "endereco_entrega")
    inlines = (ItemLocacaoInline, HistoricoLocacaoInline)


@admin.register(ItemLocacao)
class ItemLocacaoAdmin(admin.ModelAdmin):
    list_display = ("locacao", "ativo", "quantidade", "valor_diaria", "valor_total")
    search_fields = ("locacao__codigo", "ativo__codigo", "ativo__nome")
    autocomplete_fields = ("locacao", "ativo")


@admin.register(HistoricoLocacao)
class HistoricoLocacaoAdmin(admin.ModelAdmin):
    list_display = ("locacao", "tipo", "usuario_nome", "criado_em")
    list_filter = ("tipo", "criado_em")
    search_fields = ("locacao__codigo", "descricao", "usuario_nome")
    autocomplete_fields = ("locacao",)
    readonly_fields = ("criado_em",)
