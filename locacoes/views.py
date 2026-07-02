from django.db.models import Count, Q
from django.contrib import messages
from django.shortcuts import redirect, render

from config.views import with_layout

from .forms import LocacaoForm
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


def locacao_create(request):
    if request.method == "POST":
        form = LocacaoForm(request.POST)
        if form.is_valid():
            locacao = form.save()
            messages.success(request, f"Locacao {locacao.codigo} cadastrada com sucesso.")
            return redirect("locacoes")
    else:
        form = LocacaoForm()

    return render(
        request,
        "locacoes/form.html",
        with_layout(
            {
                "page_title": "Nova locacao",
                "form": form,
            }
        ),
    )
