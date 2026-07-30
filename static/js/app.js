function parseMoney(value) {
    if (!value) {
        return 0;
    }

    return Number(String(value).replace(/\./g, "").replace(",", ".")) || 0;
}

function formatMoney(value) {
    return value.toFixed(2);
}

function formatMoneyBR(value) {
    return value.toFixed(2).replace(".", ",");
}

function setCursorPosition(field, position) {
    window.requestAnimationFrame(() => {
        field.setSelectionRange(position, position);
    });
}

function formatMoneyInput(field, { padDecimals = false } = {}) {
    const value = field.value;
    const cursor = field.selectionStart ?? value.length;
    const separatorIndex = Math.max(value.lastIndexOf(","), value.lastIndexOf("."));

    if (!value.trim()) {
        return;
    }

    const hasSeparator = separatorIndex >= 0;
    const integerText = hasSeparator ? value.slice(0, separatorIndex) : value;
    const decimalText = hasSeparator ? value.slice(separatorIndex + 1) : "";
    const integerDigits = integerText.replace(/\D/g, "") || "0";
    let decimalDigits = hasSeparator ? decimalText.replace(/\D/g, "").slice(0, 2) : "00";

    if (padDecimals) {
        decimalDigits = decimalDigits.padEnd(2, "0").slice(0, 2);
    }

    const editingDecimals = hasSeparator && cursor > separatorIndex;
    const integerCursor = value.slice(0, hasSeparator ? Math.min(cursor, separatorIndex) : cursor).replace(/\D/g, "").length;
    const decimalCursor = editingDecimals ? value.slice(separatorIndex + 1, cursor).replace(/\D/g, "").length : 0;

    field.value = `${integerDigits},${decimalDigits}`;

    if (editingDecimals) {
        setCursorPosition(field, integerDigits.length + 1 + Math.min(decimalCursor, decimalDigits.length));
        return;
    }

    setCursorPosition(field, Math.min(integerCursor, integerDigits.length));
}

function setupMoneyFields() {
    document.querySelectorAll("[data-money-field='true']").forEach((field) => {
        field.addEventListener("input", () => formatMoneyInput(field));
        field.addEventListener("blur", () => formatMoneyInput(field, { padDecimals: true }));
    });
}

function setupItemLocacaoCalculator(row) {
    if (row.dataset.calculatorReady === "true") {
        return;
    }

    const quantidade = row.querySelector("[name$='quantidade']");
    const valorDiaria = row.querySelector("[name$='valor_diaria']");
    const valorTotal = row.querySelector("[name$='valor_total']");

    if (!quantidade || !valorDiaria || !valorTotal) {
        return;
    }

    const recalculate = () => {
        const total = parseMoney(quantidade.value) * parseMoney(valorDiaria.value);
        valorTotal.value = total ? formatMoney(total) : "";
    };

    quantidade.addEventListener("input", recalculate);
    valorDiaria.addEventListener("input", recalculate);
    row.dataset.calculatorReady = "true";
}

function setupItemLocacaoRows() {
    document.querySelectorAll("[data-item-locacao-form]").forEach(setupItemLocacaoCalculator);
}

function setupItemLocacaoDynamicRows() {
    const form = document.querySelector("[data-locacao-form]");

    if (!form) {
        return;
    }

    const container = form.querySelector("[data-item-locacao-formset]");
    const template = form.querySelector("[data-item-locacao-empty-form]");
    const addButton = form.querySelector("[data-add-item-locacao-row]");
    const totalForms = form.querySelector("[name='itens-TOTAL_FORMS']");

    if (!container || !template || !addButton || !totalForms) {
        return;
    }

    addButton.addEventListener("click", () => {
        const index = Number(totalForms.value);
        const html = template.innerHTML.replaceAll("__prefix__", String(index));
        const wrapper = document.createElement("div");
        wrapper.innerHTML = html.trim();
        const row = wrapper.firstElementChild;

        container.append(row);
        totalForms.value = String(index + 1);
        setupItemLocacaoCalculator(row);
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
    setupItemLocacaoRows();
    setupItemLocacaoDynamicRows();
    setupLocacaoEnderecoLoader();
    setupMoneyFields();
});
