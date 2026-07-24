function parseMoney(value) {
    if (!value) {
        return 0;
    }

    return Number(String(value).replace(/\./g, "").replace(",", ".")) || 0;
}

function formatMoney(value) {
    return value.toFixed(2);
}

function setupItemLocacaoCalculator() {
    const forms = document.querySelectorAll("[data-item-locacao-form]");

    forms.forEach((form) => {
        const quantidade = form.querySelector("[name$='quantidade']");
        const valorDiaria = form.querySelector("[name$='valor_diaria']");
        const valorTotal = form.querySelector("[name$='valor_total']");

        if (!quantidade || !valorDiaria || !valorTotal) {
            return;
        }

        const recalculate = () => {
            const total = parseMoney(quantidade.value) * parseMoney(valorDiaria.value);
            valorTotal.value = total ? formatMoney(total) : "";
        };

        quantidade.addEventListener("input", recalculate);
        valorDiaria.addEventListener("input", recalculate);
    });
}

function setupLocacaoEnderecoLoader() {
    const forms = document.querySelectorAll("[data-locacao-form]");

    forms.forEach((form) => {
        const cliente = form.querySelector("[name='cliente']");
        const endereco = form.querySelector("[name='endereco_entrega']");

        if (!cliente || !endereco) {
            return;
        }

        const clearEnderecos = () => {
            endereco.innerHTML = "";
            endereco.append(new Option("---------", ""));
        };

        const loadEnderecos = async () => {
            const clienteId = cliente.value;
            const selected = endereco.value;
            clearEnderecos();

            if (!clienteId) {
                return;
            }

            const response = await fetch(`/clientes/${clienteId}/enderecos/opcoes/`);
            const data = await response.json();

            data.enderecos.forEach((item) => {
                const option = new Option(item.label, item.id);
                option.selected = String(item.id) === selected;
                endereco.append(option);
            });
        };

        cliente.addEventListener("change", loadEnderecos);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupItemLocacaoCalculator();
    setupLocacaoEnderecoLoader();
});
