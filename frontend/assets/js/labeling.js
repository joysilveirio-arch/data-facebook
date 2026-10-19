
"use strict";

let _lp = 1;
let _ls = 10;
let _labelingLoading = false;

/**
 * Inicializa pájina manual labeling.
 */
function initLabeling() {
    loadUnlabeled();
    loadStats();
}

/**
 * Hatudu alerta.
 */
function labelingAlert(message, type = "info") {
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
 * Karrega lista post ne'ebé seidauk hetan label.
 */
async function loadUnlabeled() {
    const rows = el("rows");

    if (!rows) {
        labelingAlert("La hetan tabela tbody ho ID rows.", "err");
        return;
    }

    if (_labelingLoading) return;
    _labelingLoading = true;

    rows.innerHTML = `
        <tr>
            <td colspan="4" style="text-align:center;padding:24px;">
                Karrega post ne'ebé seidauk iha label...
            </td>
        </tr>
    `;

    try {
        const data = await api(
            `/labels/unlabeled?page=${_lp}&page_size=${_ls}`
        );

        const items = Array.isArray(data.items) ? data.items : [];
        const total = Math.max(0, Number(data.total) || 0);
        const totalPages = Math.max(1, Math.ceil(total / _ls));

        if (_lp > totalPages) {
            _lp = totalPages;
            _labelingLoading = false;
            return loadUnlabeled();
        }

        if (items.length === 0) {
            rows.innerHTML = `
                <tr>
                    <td colspan="4"
                        style="text-align:center;padding:30px;color:var(--muted);">
                        Post hotu-hotu ona iha label, ka dadus seidauk iha. 🎉
                    </td>
                </tr>
            `;
        } else {
            rows.innerHTML = items.map((record) => {
                const id = Number(record.id);
                const validId = Number.isSafeInteger(id) && id > 0;

                const text = String(record.text ?? "");
                const author = String(record.author_name ?? "N/A");

                return `
                    <tr>
                        <td>${validId ? id : "—"}</td>

                        <td title="${esc(text)}">
                            ${esc(truncate(text, 100))}
                        </td>

                        <td>${esc(author)}</td>

                        <td>
                            ${
                                validId
                                    ? `
                                        <div class="row label-actions"
                                             style="gap:6px;flex-wrap:wrap;">
                                            <button
                                                type="button"
                                                class="btn success"
                                                data-label-id="${id}"
                                                data-label-value="positive"
                                                style="padding:6px 12px;font-size:12px;">
                                                Positive
                                            </button>

                                            <button
                                                type="button"
                                                class="btn warning"
                                                data-label-id="${id}"
                                                data-label-value="neutral"
                                                style="padding:6px 12px;font-size:12px;">
                                                Neutral
                                            </button>

                                            <button
                                                type="button"
                                                class="btn danger"
                                                data-label-id="${id}"
                                                data-label-value="negative"
                                                style="padding:6px 12px;font-size:12px;">
                                                Negative
                                            </button>
                                        </div>
                                    `
                                    : `<span class="small">ID inválidu</span>`
                            }
                        </td>
                    </tr>
                `;
            }).join("");

            // Liga event handler ba kada botão label.
            rows.querySelectorAll("[data-label-id]").forEach((button) => {
                button.addEventListener("click", async () => {
                    const id = Number(button.dataset.labelId);
                    const label = button.dataset.labelValue;

                    if (
                        Number.isSafeInteger(id) &&
                        id > 0 &&
                        ["positive", "neutral", "negative"].includes(label)
                    ) {
                        await lbl(id, label, button);
                    }
                });
            });
        }

        renderLabelPager(total, totalPages);

    } catch (error) {
        rows.innerHTML = `
            <tr>
                <td colspan="4"
                    style="text-align:center;padding:24px;color:var(--muted);">
                    La konsege karrega dadus.
                </td>
            </tr>
        `;

        labelingAlert(
            error.message || "Erro bainhira karrega post.",
            "err"
        );
    } finally {
        _labelingLoading = false;
    }
}

/**
 * Render pagination.
 */
function renderLabelPager(total, totalPages) {
    const pager = el("pager");
    if (!pager) return;

    pager.innerHTML = `
        <button
            type="button"
            class="btn ghost"
            id="labelPrev"
            ${_lp <= 1 ? "disabled" : ""}>
            « Anterior
        </button>

        <span class="small" style="padding:0 10px;align-self:center;">
            Página ${_lp} husi ${totalPages} (${total} antreada)
        </span>

        <button
            type="button"
            class="btn ghost"
            id="labelNext"
            ${_lp >= totalPages ? "disabled" : ""}>
            Próximo »
        </button>
    `;

    const prev = el("labelPrev");
    const next = el("labelNext");

    if (prev) {
        prev.addEventListener("click", () => {
            if (_lp > 1) {
                _lp--;
                loadUnlabeled();
            }
        });
    }

    if (next) {
        next.addEventListener("click", () => {
            if (_lp < totalPages) {
                _lp++;
                loadUnlabeled();
            }
        });
    }
}

/**
 * Fó label manual ba post ida.
 */
async function lbl(id, label, button = null) {
    const validLabels = ["positive", "neutral", "negative"];

    if (!Number.isSafeInteger(id) || id <= 0) {
        labelingAlert("ID post inválidu.", "err");
        return;
    }

    if (!validLabels.includes(label)) {
        labelingAlert("Label sentiment la válidu.", "err");
        return;
    }

    if (button && button.disabled) return;

    const actionButtons = button
        ? button.closest("tr")?.querySelectorAll("button[data-label-id]")
        : [];

    if (actionButtons) {
        actionButtons.forEach((item) => {
            item.disabled = true;
        });
    }

    try {
        await api(`/labels/${id}`, {
            method: "POST",
            body: JSON.stringify({ label })
        });

        labelingAlert(
            `Post ID ${id} hetan label ${label} ho susesu.`,
            "ok"
        );

        // Atualiza lista no ne'ebé label foin aplika sei lakon.
        await Promise.all([
            loadUnlabeled(),
            loadStats()
        ]);

    } catch (error) {
        labelingAlert(
            error.message || "La konsege salva label.",
            "err"
        );

        if (actionButtons) {
            actionButtons.forEach((item) => {
                item.disabled = false;
            });
        }
    }
}

/**
 * Karrega estatístika label husi backend.
 */
async function loadStats() {
    const statsBox = el("stats");
    if (!statsBox) return;

    try {
        const stats = await api("/labels/stats");

        const entries = Object.entries(stats || {});
        const preferredOrder = [
            "positive",
            "neutral",
            "negative",
            "unlabeled",
            "total"
        ];

        entries.sort((a, b) => {
            const ai = preferredOrder.indexOf(a[0].toLowerCase());
            const bi = preferredOrder.indexOf(b[0].toLowerCase());

            return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
        });

        if (entries.length === 0) {
            statsBox.innerHTML = `
                <div class="card">
                    <div class="small">Estatístika seidauk disponível.</div>
                </div>
            `;
            return;
        }

        statsBox.innerHTML = entries.map(([key, value]) => {
            const normalizedKey = String(key).toLowerCase();

            const colorClass =
                normalizedKey === "positive" ? "positive" :
                normalizedKey === "negative" ? "negative" :
                normalizedKey === "neutral" ? "neutral" : "";

            const displayName = esc(
                String(key).replace(/_/g, " ")
            );

            const displayValue = esc(
                typeof value === "number"
                    ? value.toLocaleString()
                    : String(value ?? 0)
            );

            const badgeHtml = colorClass
                ? `<span class="badge ${colorClass}">${displayName}</span>`
                : "";

            return `
                <div class="card">
                    <h3>
                        ${displayName}
                        ${badgeHtml}
                    </h3>

                    <div class="value">${displayValue}</div>
                </div>
            `;
        }).join("");

    } catch (error) {
        statsBox.innerHTML = `
            <div class="card">
                <div class="small">
                    La konsege karrega estatístika.
                </div>
            </div>
        `;
    }
}
