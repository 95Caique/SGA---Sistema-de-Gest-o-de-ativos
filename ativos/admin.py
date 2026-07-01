from django.contrib import admin

from .models import Ativo, CategoriaAtivo


@admin.register(CategoriaAtivo)
class CategoriaAtivoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa", "atualizado_em")
    list_filter = ("ativa",)
    search_fields = ("nome",)


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nome",
        "categoria",
        "status",
        "permite_rastreamento",
        "localizacao_atual",
    )
    list_filter = ("status", "categoria", "permite_rastreamento")
    search_fields = ("codigo", "patrimonio", "nome", "localizacao_atual")
