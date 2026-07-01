from django.contrib import admin

from .models import ItemLocacao, Locacao


class ItemLocacaoInline(admin.TabularInline):
    model = ItemLocacao
    extra = 0
    autocomplete_fields = ("ativo",)


@admin.register(Locacao)
class LocacaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "cliente", "data_inicio", "data_fim", "status", "valor_total")
    list_filter = ("status", "data_inicio", "data_fim")
    search_fields = ("codigo", "cliente__nome", "cliente__documento")
    autocomplete_fields = ("cliente", "endereco_entrega")
    inlines = (ItemLocacaoInline,)


@admin.register(ItemLocacao)
class ItemLocacaoAdmin(admin.ModelAdmin):
    list_display = ("locacao", "ativo", "quantidade", "valor_diaria", "valor_total")
    search_fields = ("locacao__codigo", "ativo__codigo", "ativo__nome")
    autocomplete_fields = ("locacao", "ativo")
