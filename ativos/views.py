from django.db.models import Q
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from config.views import with_layout

from .forms import AtivoForm
from .models import Ativo


def equipamentos_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_validos = [status for status, _label in Ativo.Status.choices]
    ativos = Ativo.objects.select_related("categoria").order_by("codigo")

    if query:
        ativos = ativos.filter(
            Q(codigo__icontains=query)
            | Q(patrimonio__icontains=query)
            | Q(nome__icontains=query)
            | Q(categoria__nome__icontains=query)
            | Q(localizacao_atual__icontains=query)
        )

    if status_filter in status_validos:
        ativos = ativos.filter(status=status_filter)

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
                "status_filter": status_filter if status_filter in status_validos else "",
                "status_counts": status_counts,
            }
        ),
    )


def equipamento_create(request):
    if request.method == "POST":
        form = AtivoForm(request.POST)
        if form.is_valid():
            ativo = form.save()
            messages.success(request, f"Equipamento {ativo.codigo} cadastrado com sucesso.")
            return redirect("equipamentos")
    else:
        form = AtivoForm()

    return render(
        request,
        "ativos/form.html",
        with_layout(
            {
                "page_title": "Novo equipamento",
                "form_title": "Novo equipamento",
                "form_subtitle": "Cadastre um ativo locavel com status, categoria, localizacao e rastreio.",
                "submit_label": "Salvar equipamento",
                "form": form,
            }
        ),
    )


def equipamento_update(request, pk):
    ativo = get_object_or_404(Ativo, pk=pk)

    if request.method == "POST":
        form = AtivoForm(request.POST, instance=ativo)
        if form.is_valid():
            ativo = form.save()
            messages.success(request, f"Equipamento {ativo.codigo} atualizado com sucesso.")
            return redirect("equipamentos")
    else:
        form = AtivoForm(instance=ativo)

    return render(
        request,
        "ativos/form.html",
        with_layout(
            {
                "page_title": f"Editar {ativo.codigo}",
                "form_title": f"Editar equipamento {ativo.codigo}",
                "form_subtitle": "Atualize os dados cadastrais, status, localizacao e rastreio do ativo.",
                "submit_label": "Salvar alteracoes",
                "form": form,
            }
        ),
    )
