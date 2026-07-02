from django.db.models import Count, Q
from django.contrib import messages
from django.shortcuts import redirect, render

from config.views import with_layout

from .forms import ClienteForm
from .models import Cliente


def clientes_list(request):
    query = request.GET.get("q", "").strip()
    clientes = Cliente.objects.annotate(
        total_locacoes=Count("locacoes", distinct=True),
        total_contatos=Count("contatos", distinct=True),
    ).order_by("nome")

    if query:
        clientes = clientes.filter(
            Q(nome__icontains=query)
            | Q(documento__icontains=query)
            | Q(email__icontains=query)
            | Q(telefone__icontains=query)
            | Q(responsavel__icontains=query)
        )

    status_counts = {
        "todos": Cliente.objects.count(),
        "ativos": Cliente.objects.filter(status=Cliente.Status.ATIVO).count(),
        "inativos": Cliente.objects.filter(status=Cliente.Status.INATIVO).count(),
        "bloqueados": Cliente.objects.filter(status=Cliente.Status.BLOQUEADO).count(),
    }

    return render(
        request,
        "clientes/list.html",
        with_layout(
            {
                "page_title": "Clientes",
                "clientes": clientes,
                "query": query,
                "status_counts": status_counts,
            }
        ),
    )


def cliente_create(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f"Cliente {cliente.nome} cadastrado com sucesso.")
            return redirect("clientes")
    else:
        form = ClienteForm()

    return render(
        request,
        "clientes/form.html",
        with_layout(
            {
                "page_title": "Novo cliente",
                "form": form,
            }
        ),
    )
