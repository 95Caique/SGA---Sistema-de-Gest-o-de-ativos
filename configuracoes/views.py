from django.contrib import messages
from django.shortcuts import redirect, render

from config.views import with_layout

from .forms import EmpresaConfigForm
from .services import empresa_atual


def configuracoes_empresa(request):
    if not request.user.is_superuser:
        messages.error(request, "Apenas superusuarios podem acessar as configuracoes da empresa.")
        return redirect("dashboard")

    empresa = empresa_atual()

    if request.method == "POST":
        form = EmpresaConfigForm(request.POST, instance=empresa)

        if form.is_valid():
            form.save()
            messages.success(request, "Configuracoes da empresa atualizadas com sucesso.")
            return redirect("configuracoes_empresa")
    else:
        form = EmpresaConfigForm(instance=empresa)

    return render(
        request,
        "configuracoes/empresa_form.html",
        with_layout(
            {
                "page_title": "Configuracoes",
                "form": form,
                "empresa": empresa,
            }
        ),
    )
