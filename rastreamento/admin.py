from django.contrib import admin

from .models import PosicaoRastreamento, Rastreador


@admin.register(Rastreador)
class RastreadorAdmin(admin.ModelAdmin):
    list_display = (
        "identificador",
        "ativo",
        "status",
        "bateria_percentual",
        "sinal_gsm_percentual",
        "usando_dados_simulados",
        "atualizado_em",
    )
    list_filter = ("status", "usando_dados_simulados")
    search_fields = ("identificador", "ativo__codigo", "ativo__nome")


@admin.register(PosicaoRastreamento)
class PosicaoRastreamentoAdmin(admin.ModelAdmin):
    list_display = (
        "rastreador",
        "latitude",
        "longitude",
        "velocidade_kmh",
        "registrada_em",
    )
    list_filter = ("rastreador__status",)
    search_fields = ("rastreador__identificador", "rastreador__ativo__codigo", "endereco_referencia")
