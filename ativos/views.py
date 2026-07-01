from django.db.models import Q
from django.shortcuts import render

from config.views import with_layout

from .models import Ativo


def equipamentos_list(request):
    query = request.GET.get("q", "").strip()
    ativos = Ativo.objects.select_related("categoria").order_by("codigo")

    if query:
        ativos = ativos.filter(
            Q(codigo__icontains=query)
            | Q(patrimonio__icontains=query)
            | Q(nome__icontains=query)
            | Q(categoria__nome__icontains=query)
            | Q(localizacao_atual__icontains=query)
        )

    status_counts = {
        "todos": Ativo.objects.count(),
        "disponiveis": Ativo.objects.filter(status=Ativo.Status.DISPONIVEL).count(),
        "locados": Ativo.objects.filter(status=Ativo.Status.LOCADO).count(),
        "manutencao": Ativo.objects.filter(status=Ativo.Status.MANUTENCAO).count(),
        "inativos": Ativo.objects.filter(status=Ativo.Status.INATIVO).count(),
    }

    return render(
        request,
        "ativos/list.html",
        with_layout(
            {
                "page_title": "Equipamentos",
                "ativos": ativos,
                "query": query,
                "status_counts": status_counts,
            }
        ),
    )
