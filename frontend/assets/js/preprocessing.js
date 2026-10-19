
"use strict";

/**
 * Inicializa pájina Preprocessing.
 */
function initPreprocessing() {
    const btnRun = el("btnRun");
    const btnPreview = el("btnPv");
    const limitInput = el("limit");

    if (btnRun) {
        btnRun.addEventListener("click", run);
    }

    if (btnPreview) {
        btnPreview.addEventListener("click", preview);
    }

    // Ctrl + Enter atu halo preview.
    const previewInput = el("pv");

    if (previewInput) {
        previewInput.addEventListener("keydown", (event) => {
            if (event.ctrlKey && event.key === "Enter") {
                preview();
            }
        });
    }

    // Limit tenke númeru pozitivu ka mamuk.
    if (limitInput) {
        limitInput.min = "1";
        limitInput.step = "1";
    }
}

/**
 * Hatudu alerta ho seguransa.
 */
function preprocessingAlert(message, type = "info") {
    const alertBox = el("alert");
    if (!alertBox) return;

    const safeType = ["ok", "err", "info", "warning"].includes(type)
        ? type
        : "info";

    alertBox.innerHTML = `
        <div class="alert ${safeType}">
            ${esc(message)}
        </div>
    `;
}

/**
 * Prosesu dataset ba preprocessing.
 */
async function run() {
    const btnRun = el("btnRun");
    const rows = el("rows");
    const limitInput = el("limit");
    const forceInput = el("force");

    if (!rows) {
        preprocessingAlert(
            "La hetan tabela rezultadu ho ID rows.",
            "err"
        );
        return;
    }

    if (!forceInput) {
        preprocessingAlert(
            "La hetan input ho ID force.",
            "err"
        );
        return;
    }

    let limit = null;

    if (limitInput && limitInput.value.trim() !== "") {
        limit = Number(limitInput.value);

        if (!Number.isSafeInteger(limit) || limit < 1) {
            preprocessingAlert(
                "Limit tenke númeru inteiru boot liu zero.",
                "warning"
            );
            limitInput.focus();
            return;
        }
    }

    const originalButtonText = btnRun
        ? btnRun.textContent
        : "";

    if (btnRun) {
        btnRun.disabled = true;
        btnRun.textContent = "Prosesu hela...";
    }

    preprocessingAlert(
        "Preprocessing dataset prosesu hela. Favór hein...",
        "info"
    );

    rows.innerHTML = `
        <tr>
            <td colspan="3" style="text-align:center;padding:24px;">
                Prosesu teksu...
            </td>
        </tr>
    `;

    try {
        const result = await api("/preprocessing/run", {
            method: "POST",
            body: JSON.stringify({
                limit,
                force: forceInput.checked
            })
        });

        const items = Array.isArray(result.items)
            ? result.items
            : [];

        if (items.length === 0) {
            rows.innerHTML = `
                <tr>
                    <td colspan="3"
                        style="text-align:center;color:var(--muted);padding:24px;">
                        La iha dadus ne'ebé prosesu iha resposta.
                    </td>
                </tr>
            `;
        } else {
            rows.innerHTML = items.map((item) => {
                const id = Number(item.id);
                const safeId = Number.isSafeInteger(id) ? id : "—";

                const originalText = String(item.text ?? "");
                const cleanedText = String(item.text_clean ?? "");

                return `
                    <tr>
                        <td>${safeId}</td>

                        <td title="${esc(originalText)}">
                            ${esc(truncate(originalText, 80))}
                        </td>

                        <td title="${esc(cleanedText)}">
                            ${esc(truncate(cleanedText, 80))}
                        </td>
                    </tr>
                `;
            }).join("");
        }

        const processed = Number(result.processed);

        preprocessingAlert(
            `Preprocessing remata. Dadus prosesadu: ${
                Number.isFinite(processed) && processed >= 0
                    ? processed.toLocaleString()
                    : items.length.toLocaleString()
            }.`,
            "ok"
        );

    } catch (error) {
        rows.innerHTML = `
            <tr>
                <td colspan="3"
                    style="text-align:center;color:var(--muted);padding:24px;">
                    La konsege prosesu dadus.
                </td>
            </tr>
        `;

        preprocessingAlert(
            error.message || "Erro bainhira halo preprocessing.",
            "err"
        );
    } finally {
        if (btnRun) {
            btnRun.disabled = false;
            btnRun.textContent = originalButtonText || "Run Preprocessing";
        }
    }
}

/**
 * Preview limpeza teksu ida, laiha alterasaun ba dataset tomak.
 */
async function preview() {
    const input = el("pv");
    const output = el("pvOut");
    const btnPreview = el("btnPv");

    if (!input || !output) {
        preprocessingAlert(
            "La hetan input pv ka rezultadu pvOut iha HTML.",
            "err"
        );
        return;
    }

    const text = input.value.trim();

    if (!text) {
        output.innerHTML = `
            <div class="alert warning">
                Favor hatama testu antes halo preview.
            </div>
        `;

        input.focus();
        return;
    }

    const originalButtonText = btnPreview
        ? btnPreview.textContent
        : "";

    if (btnPreview) {
        btnPreview.disabled = true;
        btnPreview.textContent = "Analiza hela...";
    }

    output.innerHTML = `
        <div class="panel">
            <p class="small">Sistema limpa testu hela...</p>
        </div>
    `;

    try {
        const result = await api("/preprocessing/preview", {
            method: "POST",
            body: JSON.stringify({ text })
        });

        const cleanText = String(result.clean ?? "");

        output.innerHTML = `
            <div class="panel" style="margin-top:10px;">
                <div class="small" style="margin-bottom:8px;">
                    Rezultadu Teksu Limpu
                </div>

                <div style="white-space:pre-wrap;overflow-wrap:anywhere;
                            background:var(--bg);padding:14px;border-radius:8px;
                            border:1px solid var(--border);
                            font-family:monospace;">
                    ${esc(cleanText)}
                </div>

                <div class="small" style="margin-top:10px;">
                    Karakter orijinál: ${text.length.toLocaleString()}
                    <span style="padding:0 6px;">|</span>
                    Karakter limpu: ${cleanText.length.toLocaleString()}
                </div>
            </div>
        `;

    } catch (error) {
        output.innerHTML = `
            <div class="alert err" style="margin-top:10px;">
                ${esc(error.message || "La konsege halo preview.")}
            </div>
        `;
    } finally {
        if (btnPreview) {
            btnPreview.disabled = false;
            btnPreview.textContent = originalButtonText || "Preview Teksu";
        }
    }
}
