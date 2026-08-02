from .models import EmpresaConfig


def empresa_atual():
    return EmpresaConfig.atual()
