"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from ativos.views import equipamento_create, equipamentos_list
from clientes.views import cliente_create, clientes_list
from locacoes.views import locacao_ativar, locacao_create, locacao_detail, locacoes_list
from rastreamento.views import rastreamento_mapa

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('agenda/', views.module_page, {'module': 'agenda'}, name='agenda'),
    path('locacoes/', locacoes_list, name='locacoes'),
    path('locacoes/nova/', locacao_create, name='locacao_create'),
    path('locacoes/<int:pk>/ativar/', locacao_ativar, name='locacao_ativar'),
    path('locacoes/<int:pk>/', locacao_detail, name='locacao_detail'),
    path('equipamentos/', equipamentos_list, name='equipamentos'),
    path('equipamentos/novo/', equipamento_create, name='equipamento_create'),
    path('clientes/', clientes_list, name='clientes'),
    path('clientes/novo/', cliente_create, name='cliente_create'),
    path('contratos/', views.module_page, {'module': 'contratos'}, name='contratos'),
    path('financeiro/', views.module_page, {'module': 'financeiro'}, name='financeiro'),
    path('manutencao/', views.module_page, {'module': 'manutencao'}, name='manutencao'),
    path('rastreamento/', rastreamento_mapa, name='rastreamento'),
    path('alertas/', views.module_page, {'module': 'alertas'}, name='alertas'),
    path('relatorios/', views.module_page, {'module': 'relatorios'}, name='relatorios'),
    path('admin/', admin.site.urls),
]
