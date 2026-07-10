from django.contrib import admin

from .models import OrdemManutencao


@admin.register(OrdemManutencao)
class OrdemManutencaoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "ativo", "tipo", "status", "prioridade", "data_abertura", "data_prevista"]
    list_filter = ["status", "tipo", "prioridade"]
    search_fields = ["codigo", "ativo__codigo", "ativo__nome", "responsavel"]
