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

from agenda.views import agenda_list
from alertas.views import alertas_list
from ativos.views import equipamento_create, equipamento_update, equipamentos_list
from clientes.views import (
    cliente_contato_create,
    cliente_contato_update,
    cliente_create,
    cliente_endereco_create,
    cliente_endereco_update,
    cliente_update,
    clientes_list,
)
from contratos.views import contratos_list
from financeiro.views import financeiro_list
from locacoes.views import (
    locacao_ativar,
    locacao_cancelar,
    locacao_create,
    locacao_detail,
    locacao_finalizar,
    locacao_item_remove,
    locacao_update,
    locacoes_list,
    orcamento_aprovar,
    orcamento_pdf,
    orcamentos_list,
)
from manutencao.views import (
    manutencao_cancelar,
    manutencao_create,
    manutencao_finalizar,
    manutencao_iniciar,
    manutencoes_list,
)
from rastreamento.views import rastreamento_mapa
from relatorios.views import relatorios_list

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('agenda/', agenda_list, name='agenda'),
    path('locacoes/', locacoes_list, name='locacoes'),
    path('locacoes/nova/', locacao_create, name='locacao_create'),
    path('locacoes/<int:pk>/editar/', locacao_update, name='locacao_update'),
    path('locacoes/<int:pk>/ativar/', locacao_ativar, name='locacao_ativar'),
    path('locacoes/<int:pk>/cancelar/', locacao_cancelar, name='locacao_cancelar'),
    path('locacoes/<int:pk>/finalizar/', locacao_finalizar, name='locacao_finalizar'),
    path('locacoes/<int:pk>/itens/<int:item_pk>/remover/', locacao_item_remove, name='locacao_item_remove'),
    path('locacoes/<int:pk>/', locacao_detail, name='locacao_detail'),
    path('orcamentos/', orcamentos_list, name='orcamentos'),
    path('orcamentos/<int:pk>/aprovar/', orcamento_aprovar, name='orcamento_aprovar'),
    path('orcamentos/<int:pk>/pdf/', orcamento_pdf, name='orcamento_pdf'),
    path('equipamentos/', equipamentos_list, name='equipamentos'),
    path('equipamentos/novo/', equipamento_create, name='equipamento_create'),
    path('equipamentos/<int:pk>/editar/', equipamento_update, name='equipamento_update'),
    path('clientes/', clientes_list, name='clientes'),
    path('clientes/novo/', cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/contatos/novo/', cliente_contato_create, name='cliente_contato_create'),
    path(
        'clientes/<int:pk>/contatos/<int:contato_pk>/editar/',
        cliente_contato_update,
        name='cliente_contato_update',
    ),
    path('clientes/<int:pk>/enderecos/novo/', cliente_endereco_create, name='cliente_endereco_create'),
    path(
        'clientes/<int:pk>/enderecos/<int:endereco_pk>/editar/',
        cliente_endereco_update,
        name='cliente_endereco_update',
    ),
    path('contratos/', contratos_list, name='contratos'),
    path('financeiro/', financeiro_list, name='financeiro'),
    path('manutencao/', manutencoes_list, name='manutencao'),
    path('manutencao/nova/', manutencao_create, name='manutencao_create'),
    path('manutencao/<int:pk>/iniciar/', manutencao_iniciar, name='manutencao_iniciar'),
    path('manutencao/<int:pk>/finalizar/', manutencao_finalizar, name='manutencao_finalizar'),
    path('manutencao/<int:pk>/cancelar/', manutencao_cancelar, name='manutencao_cancelar'),
    path('rastreamento/', rastreamento_mapa, name='rastreamento'),
    path('alertas/', alertas_list, name='alertas'),
    path('relatorios/', relatorios_list, name='relatorios'),
    path('admin/', admin.site.urls),
]
