
"use strict";

/**
 * Inicializa pájina Prediction.
 */
function initPrediction() {
    const btnPredict = el("btnPredict");
    const btnApplyAll = el("btnApplyAll");
    const textInput = el("text");

    if (btnPredict) {
        btnPredict.addEventListener("click", predict);
    }

    if (btnApplyAll) {
        btnApplyAll.addEventListener("click", applyAll);
    }

    if (textInput) {
        textInput.addEventListener("keydown", (event) => {
            if (event.ctrlKey && event.key === "Enter") {
                predict();
            }
        });
    }
}

/**
 * Hatudu alerta ho seguransa.
 */
function predictionAlert(message, type = "info") {
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
 * Konverte valor ba númeru iha interval 0-1.
 */
function predictionProbability(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) return null;

    // Backend normalmente retorna probabilidades entre 0 no 1.
    return Math.min(1, Math.max(0, number));
}

/**
 * Predisaun sentiment ba testu ida.
 */
async function predict() {
    const textInput = el("text");
    const output = el("out");
    const btnPredict = el("btnPredict");

    if (!textInput || !output) {
        predictionAlert(
            "La hetan elementu HTML ho ID text ka out.",
            "err"
        );
        return;
    }

    const text = textInput.value.trim();

    if (!text) {
        predictionAlert("Teksu labele mamuk.", "warning");
        textInput.focus();
        return;
    }

    const originalButtonText = btnPredict
        ? btnPredict.textContent
        : "";

    if (btnPredict) {
        btnPredict.disabled = true;
        btnPredict.textContent = "Analiza sentiment...";
    }

    predictionAlert("Sistema halo análise sentiment...", "info");

    output.innerHTML = `
        <div class="panel">
            <p class="small">Prosesu predisaun hela. Favór hein...</p>
        </div>
    `;

    try {
        const result = await api("/predict/", {
            method: "POST",
            body: JSON.stringify({ text })
        });

        const label = String(result.label ?? "unknown").toLowerCase();
        const validLabels = ["positive", "neutral", "negative"];

        if (!validLabels.includes(label)) {
            throw new Error(
                "Resposta backend la iha label sentiment ne'ebé válidu."
            );
        }

        const confidence = predictionProbability(result.confidence);

        const cleanText = String(result.clean ?? "");
        const probabilities =
            result.probabilities &&
            typeof result.probabilities === "object"
                ? result.probabilities
                : {};

        const colorMap = {
            positive: "var(--success)",
            neutral: "var(--warning)",
            negative: "var(--danger)"
        };

        const labelNames = {
            positive: "Positive",
            neutral: "Neutral",
            negative: "Negative"
        };

        const probabilityEntries = Object.entries(probabilities)
            .filter(([key]) => validLabels.includes(key.toLowerCase()))
            .map(([key, value]) => ({
                key: key.toLowerCase(),
                probability: predictionProbability(value)
            }))
            .filter((item) => item.probability !== null);

        const probabilityHtml = probabilityEntries.length
            ? probabilityEntries.map((item) => {
                const percentage = (item.probability * 100).toFixed(2);
                const color = colorMap[item.key];

                return `
                    <div style="margin-bottom:16px;">
                        <div class="row"
                             style="justify-content:space-between;margin-bottom:6px;">
                            <span>${labelNames[item.key]}</span>
                            <strong>${percentage}%</strong>
                        </div>

                        <div
                            role="progressbar"
                            aria-label="${labelNames[item.key]} probability"
                            aria-valuemin="0"
                            aria-valuemax="100"
                            aria-valuenow="${percentage}"
                            style="width:100%;height:9px;background:var(--border);
                                   border-radius:6px;overflow:hidden;">
                            <div style="width:${percentage}%;height:100%;
                                        background:${color};border-radius:6px;">
                            </div>
                        </div>
                    </div>
                `;
            }).join("")
            : `
                <p class="small">
                    Backend la fó informasaun probabilidades ba predisaun ida-ne'e.
                </p>
            `;

        const confidenceHtml = confidence !== null
            ? `${(confidence * 100).toFixed(2)}%`
            : "La disponível";

        output.innerHTML = `
            <div class="panel">
                <div class="row"
                     style="justify-content:space-between;align-items:center;gap:12px;">
                    <div>
                        <div class="small">Sentiment Preditu</div>
                        <div style="margin-top:8px;">
                            ${badge(label)}
                        </div>
                    </div>

                    <div style="text-align:right;">
                        <div class="small">Confidence</div>
                        <div class="value">${confidenceHtml}</div>
                    </div>
                </div>

                <div class="divider" style="margin:20px 0;"></div>

                <h3>Testu Limpu</h3>

                <div style="font-family:monospace;white-space:pre-wrap;
                            overflow-wrap:anywhere;background:var(--bg);
                            padding:14px;border-radius:8px;">
                    ${esc(cleanText || "La iha testu limpu iha resposta backend.")}
                </div>

                <h3 style="margin-top:24px;">Probabilidade Sentiment</h3>

                ${probabilityHtml}
            </div>
        `;

        const alertBox = el("alert");
        if (alertBox) alertBox.innerHTML = "";

    } catch (error) {
        predictionAlert(
            error.message || "Predisaun sentiment falla.",
            "err"
        );

        output.innerHTML = `
            <div class="panel">
                <p class="small">
                    La konsege halo predisaun. Verifika backend, modelu
                    ne'ebé treinu ona no ligasaun API.
                </p>
            </div>
        `;
    } finally {
        if (btnPredict) {
            btnPredict.disabled = false;
            btnPredict.textContent = originalButtonText || "Prediksi Sentiment";
        }
    }
}

/**
 * Aplika predisaun ba record hotu iha backend.
 */
async function applyAll() {
    const btnApplyAll = el("btnApplyAll");
    const output = el("out");

    const confirmed = confirm(
        "Aplika predisaun ba record hotu? " +
        "Prosesu ne'e bele demora depende ba quantidade dadus."
    );

    if (!confirmed) return;

    const originalButtonText = btnApplyAll
        ? btnApplyAll.textContent
        : "";

    if (btnApplyAll) {
        btnApplyAll.disabled = true;
        btnApplyAll.textContent = "Atualiza record...";
    }

    predictionAlert("Predisaun ba record hotu prosesu hela...", "info");

    try {
        const result = await api("/predict/apply-all", {
            method: "POST"
        });

        const updated = Number(result.updated);

        if (!Number.isFinite(updated) || updated < 0) {
            throw new Error(
                "Resposta backend la hatudu total record ne'ebé atualiza."
            );
        }

        if (output) {
            output.innerHTML = `
                <div class="panel">
                    <h3>Predisaun Remata</h3>
                    <div class="value">${updated.toLocaleString()}</div>
                    <p class="small">Record atualizadu tuir resposta backend.</p>
                </div>
            `;
        }

        predictionAlert(
            `Prosesu remata. Record atualizadu: ${updated.toLocaleString()}.`,
            "ok"
        );

    } catch (error) {
        predictionAlert(
            error.message || "La konsege aplika predisaun ba record hotu.",
            "err"
        );
    } finally {
        if (btnApplyAll) {
            btnApplyAll.disabled = false;
            btnApplyAll.textContent = originalButtonText || "Aplika ba Record Hotu";
        }
    }
}
