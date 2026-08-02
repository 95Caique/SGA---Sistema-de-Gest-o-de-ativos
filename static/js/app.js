function parseMoney(value) {
    if (!value) {
        return 0;
    }

    return Number(String(value).replace(/\./g, "").replace(",", ".")) || 0;
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

function setupMoneyFields(root = document) {
    root.querySelectorAll("[data-money-field='true']").forEach((field) => {
        if (field.dataset.moneyReady === "true") {
            return;
        }

        field.addEventListener("input", () => formatMoneyInput(field));
        field.addEventListener("blur", () => formatMoneyInput(field, { padDecimals: true }));
        field.dataset.moneyReady = "true";
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
        valorTotal.value = total ? formatMoneyBR(total) : "";
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
        setupMoneyFields(row);
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

function setupMaintenanceAssetDetails() {
    const panel = document.querySelector("[data-maintenance-asset-panel]");

    if (!panel) {
        return;
    }

    const form = panel.closest("form");
    const select = form ? form.querySelector("[name='ativo']") : null;
    const details = panel.querySelectorAll("[data-maintenance-asset-detail]");

    if (!select || !details.length) {
        return;
    }

    const showSelected = () => {
        details.forEach((detail) => {
            detail.hidden = detail.dataset.maintenanceAssetDetail !== select.value;
        });

        panel.classList.toggle("is-selected", Boolean(select.value));
    };

    select.addEventListener("change", showSelected);
    showSelected();
}

function setupTrackingMap() {
    const canvas = document.querySelector("#tracking-map-canvas");
    const data = document.querySelector("#tracking-map-data");

    if (!canvas || !data) {
        return;
    }

    if (!window.L) {
        canvas.innerHTML = "<div class=\"map-empty\"><strong>Mapa indisponivel</strong><p>Nao foi possivel carregar a biblioteca de mapas.</p></div>";
        return;
    }

    const points = JSON.parse(data.textContent || "[]");

    if (!points.length) {
        return;
    }

    const map = window.L.map(canvas, {
        zoomControl: true,
        scrollWheelZoom: false,
    });
    const bounds = [];

    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap",
        maxZoom: 19,
    }).addTo(map);

    points.forEach((point) => {
        const latLng = [point.lat, point.lng];
        const marker = window.L.marker(latLng, {
            icon: trackingMarkerIcon(point),
        }).addTo(map);

        marker.bindPopup(trackingPopup(point));
        bounds.push(latLng);
    });

    if (bounds.length === 1) {
        map.setView(bounds[0], 13);
        return;
    }

    map.fitBounds(bounds, { padding: [42, 42], maxZoom: 14 });
}

function trackingMarkerIcon(point) {
    const initials = String(point.code || point.name || "?").slice(0, 2).toUpperCase();
    const speedText = point.status === "online" ? `${point.speed} km/h` : point.statusLabel;
    const html = `
        <div class="tracking-marker tracking-marker-${point.status}">
            <span class="tracking-marker-icon">${initials}</span>
            <div>
                <strong>${escapeHtml(point.name)}</strong>
                <small>${escapeHtml(speedText)}</small>
            </div>
        </div>
    `;

    return window.L.divIcon({
        className: "tracking-marker-wrap",
        html,
        iconSize: [180, 46],
        iconAnchor: [18, 18],
        popupAnchor: [0, -18],
    });
}

function trackingPopup(point) {
    return `
        <div class="tracking-popup">
            <strong>${escapeHtml(point.name)}</strong>
            <span>${escapeHtml(point.code)} | ${escapeHtml(point.statusLabel)}</span>
            <span>${escapeHtml(point.address)}</span>
            <span>${escapeHtml(point.client || "Sem cliente vinculado")}</span>
            <span>Bateria ${point.battery}% | Sinal ${point.signal}%</span>
        </div>
    `;
}

function escapeHtml(value) {
    const node = document.createElement("span");
    node.textContent = String(value ?? "");
    return node.innerHTML;
}

document.addEventListener("DOMContentLoaded", () => {
    setupItemLocacaoRows();
    setupItemLocacaoDynamicRows();
    setupLocacaoEnderecoLoader();
    setupMoneyFields();
    setupMaintenanceAssetDetails();
    setupTrackingMap();
});
