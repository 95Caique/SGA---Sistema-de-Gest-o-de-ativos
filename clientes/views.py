from django.db.models import Count, Q
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from config.views import with_layout

from .forms import ClienteForm, ContatoClienteForm, EnderecoClienteForm
from .models import Cliente, ContatoCliente, EnderecoCliente


def clientes_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    status_validos = [status for status, _label in Cliente.Status.choices]
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

    if status_filter in status_validos:
        clientes = clientes.filter(status=status_filter)

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
                "status_filter": status_filter if status_filter in status_validos else "",
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
                "form_title": "Novo cliente",
                "form_subtitle": "Cadastre os dados principais do cliente para locacoes, contratos e financeiro.",
                "submit_label": "Salvar cliente",
                "form": form,
            }
        ),
    )


def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    enderecos = cliente.enderecos.order_by("-principal", "nome")
    contatos = cliente.contatos.order_by("-principal", "nome")

    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f"Cliente {cliente.nome} atualizado com sucesso.")
            return redirect("clientes")
    else:
        form = ClienteForm(instance=cliente)

    return render(
        request,
        "clientes/form.html",
        with_layout(
            {
                "page_title": f"Editar {cliente.nome}",
                "form_title": f"Editar cliente {cliente.nome}",
                "form_subtitle": "Atualize os dados principais do cliente.",
                "submit_label": "Salvar alteracoes",
                "form": form,
                "cliente": cliente,
                "enderecos": enderecos,
                "contatos": contatos,
            }
        ),
    )


def cliente_endereco_create(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    locacao_retorno = _locacao_retorno(cliente, request.GET.get("locacao"))

    if request.method == "POST":
        form = EnderecoClienteForm(request.POST)
        if form.is_valid():
            endereco = form.save(commit=False)
            endereco.cliente = cliente
            endereco.save()

            if endereco.principal:
                EnderecoCliente.objects.filter(cliente=cliente).exclude(pk=endereco.pk).update(principal=False)

            messages.success(request, f"Endereco {endereco.nome} cadastrado para {cliente.nome}.")
            if locacao_retorno:
                locacao_retorno.endereco_entrega = endereco
                locacao_retorno.save(update_fields=["endereco_entrega", "atualizado_em"])
                return redirect("locacao_update", pk=locacao_retorno.pk)

            return redirect("cliente_update", pk=cliente.pk)
    else:
        form = EnderecoClienteForm()

    return_url = reverse("locacao_update", kwargs={"pk": locacao_retorno.pk}) if locacao_retorno else reverse(
        "cliente_update", kwargs={"pk": cliente.pk}
    )

    return render(
        request,
        "clientes/endereco_form.html",
        with_layout(
            {
                "page_title": f"Novo endereco - {cliente.nome}",
                "cliente": cliente,
                "form": form,
                "return_url": return_url,
            }
        ),
    )


def cliente_enderecos_options(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    enderecos = cliente.enderecos.order_by("-principal", "nome")

    return JsonResponse(
        {
            "enderecos": [
                {
                    "id": endereco.pk,
                    "label": str(endereco),
                }
                for endereco in enderecos
            ]
        }
    )


def _locacao_retorno(cliente, locacao_id):
    if not locacao_id:
        return None

    from locacoes.models import Locacao

    return Locacao.objects.filter(
        pk=locacao_id,
        cliente=cliente,
        status__in=[Locacao.Status.ORCAMENTO, Locacao.Status.AGENDADA],
    ).first()


def cliente_endereco_update(request, pk, endereco_pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    endereco = get_object_or_404(EnderecoCliente, pk=endereco_pk, cliente=cliente)

    if request.method == "POST":
        form = EnderecoClienteForm(request.POST, instance=endereco)
        if form.is_valid():
            endereco = form.save()

            if endereco.principal:
                EnderecoCliente.objects.filter(cliente=cliente).exclude(pk=endereco.pk).update(principal=False)

            messages.success(request, f"Endereco {endereco.nome} atualizado com sucesso.")
            return redirect("cliente_update", pk=cliente.pk)
    else:
        form = EnderecoClienteForm(instance=endereco)

    return render(
        request,
        "clientes/endereco_form.html",
        with_layout(
            {
                "page_title": f"Editar endereco - {cliente.nome}",
                "form_title": f"Editar endereco {endereco.nome}",
                "submit_label": "Salvar alteracoes",
                "cliente": cliente,
                "form": form,
                "return_url": reverse("cliente_update", kwargs={"pk": cliente.pk}),
            }
        ),
    )


def cliente_contato_create(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        form = ContatoClienteForm(request.POST)
        if form.is_valid():
            contato = form.save(commit=False)
            contato.cliente = cliente
            contato.save()

            if contato.principal:
                ContatoCliente.objects.filter(cliente=cliente).exclude(pk=contato.pk).update(principal=False)

            messages.success(request, f"Contato {contato.nome} cadastrado para {cliente.nome}.")
            return redirect("cliente_update", pk=cliente.pk)
    else:
        form = ContatoClienteForm()

    return render(
        request,
        "clientes/contato_form.html",
        with_layout(
            {
                "page_title": f"Novo contato - {cliente.nome}",
                "cliente": cliente,
                "form": form,
            }
        ),
    )


def cliente_contato_update(request, pk, contato_pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    contato = get_object_or_404(ContatoCliente, pk=contato_pk, cliente=cliente)

    if request.method == "POST":
        form = ContatoClienteForm(request.POST, instance=contato)
        if form.is_valid():
            contato = form.save()

            if contato.principal:
                ContatoCliente.objects.filter(cliente=cliente).exclude(pk=contato.pk).update(principal=False)

            messages.success(request, f"Contato {contato.nome} atualizado com sucesso.")
            return redirect("cliente_update", pk=cliente.pk)
    else:
        form = ContatoClienteForm(instance=contato)

    return render(
        request,
        "clientes/contato_form.html",
        with_layout(
            {
                "page_title": f"Editar contato - {cliente.nome}",
                "form_title": f"Editar contato {contato.nome}",
                "submit_label": "Salvar alteracoes",
                "cliente": cliente,
                "form": form,
            }
        ),
    )
