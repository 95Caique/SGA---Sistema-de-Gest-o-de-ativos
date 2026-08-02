from django.contrib import admin

from .models import EmpresaConfig


@admin.register(EmpresaConfig)
class EmpresaConfigAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "razao_social", "documento", "email", "atualizado_em")
    search_fields = ("nome_fantasia", "razao_social", "documento", "email")
