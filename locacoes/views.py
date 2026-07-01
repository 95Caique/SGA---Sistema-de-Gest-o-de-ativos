from django.db.models import Count, Q
from django.shortcuts import render

from config.views import with_layout

from .models import Locacao


def locacoes_list(request):
    query = request.GET.get("q", "").strip()
    locacoes = Locacao.objects.select_related("cliente").annotate(total_itens=Count("itens")).order_by("-data_inicio")

    if query:
        locacoes = locacoes.filter(
            Q(codigo__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__documento__icontains=query)
            | Q(observacoes__icontains=query)
        )

    status_counts = {
        "todos": Locacao.objects.count(),
        "ativas": Locacao.objects.filter(status=Locacao.Status.ATIVA).count(),
        "agendadas": Locacao.objects.filter(status=Locacao.Status.AGENDADA).count(),
        "finalizadas": Locacao.objects.filter(status=Locacao.Status.FINALIZADA).count(),
        "canceladas": Locacao.objects.filter(status=Locacao.Status.CANCELADA).count(),
    }

    return render(
        request,
        "locacoes/list.html",
        with_layout(
            {
                "page_title": "Locacoes",
                "locacoes": locacoes,
                "query": query,
                "status_counts": status_counts,
            }
        ),
    )
