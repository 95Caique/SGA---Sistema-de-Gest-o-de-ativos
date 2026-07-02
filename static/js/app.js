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
        const quantidade = form.querySelector("[name='quantidade']");
        const valorDiaria = form.querySelector("[name='valor_diaria']");
        const valorTotal = form.querySelector("[name='valor_total']");

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

document.addEventListener("DOMContentLoaded", () => {
    setupItemLocacaoCalculator();
});
