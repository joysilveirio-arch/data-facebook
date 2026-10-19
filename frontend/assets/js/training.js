
"use strict";

/*
 * Facebook Sentiment - Training Model Dashboard
 *
 * Endpoints ne'ebé uza ona:
 * POST /api/v1/training/train
 * GET  /api/v1/training/status
 *
 * Presiza:
 * - assets/js/api.js ho helper api()
 * - Chart.js karrega iha training.html
 */

let trainingMetricChart = null;
let trainingDistributionChart = null;
let trainingInitialized = false;

/* =========================================================
   1. UTILITIES
========================================================= */

function trainingEl(id) {
    return document.getElementById(id);
}

function trainingEscape(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[char];
    });
}

function trainingAlert(message, type = "info") {
    const box = trainingEl("alert");
    if (!box) return;

    const allowed = ["ok", "err", "info", "warning"];
    const safeType = allowed.includes(type) ? type : "info";

    box.innerHTML = `
        <div class="alert ${safeType}" role="status">
            ${trainingEscape(message)}
        </div>
    `;
}

function trainingClearAlert() {
    const box = trainingEl("alert");
    if (box) box.innerHTML = "";
}

function trainingIsNumber(value) {
    return (
        value !== null &&
        value !== undefined &&
        value !== "" &&
        typeof value !== "boolean" &&
        Number.isFinite(Number(value))
    );
}

function trainingNumber(value) {
    if (!trainingIsNumber(value)) return "N/A";

    return Number(value).toLocaleString();
}

function trainingPercent(value) {
    if (!trainingIsNumber(value)) return "N/A";

    const number = Number(value);

    if (number < 0 || number > 1) return "N/A";

    return `${(number * 100).toFixed(2)}%`;
}

function trainingSetModelBadge(ready, label) {
    const badge = trainingEl("modelBadgeText");
    const dot = trainingEl("modelDot");

    if (badge) badge.textContent = label;

    if (dot) {
        dot.classList.toggle("ready", ready === true);
    }
}

function trainingEmpty(message) {
    return `
        <div class="training-empty">
            ${trainingEscape(message)}
        </div>
    `;
}

function trainingRenderKpi(label, value, note = "") {
    return `
        <div class="training-kpi">
            <div class="training-kpi-label">
                ${trainingEscape(label)}
            </div>
            <div class="training-kpi-value">
                ${trainingEscape(value)}
            </div>
            <div class="training-kpi-note">
                ${trainingEscape(note)}
            </div>
        </div>
    `;
}

function trainingDestroyCharts() {
    if (trainingMetricChart) {
        trainingMetricChart.destroy();
        trainingMetricChart = null;
    }

    if (trainingDistributionChart) {
        trainingDistributionChart.destroy();
        trainingDistributionChart = null;
    }
}

/* =========================================================
   2. READ METRICS FROM REAL BACKEND RESPONSE
========================================================= */

function trainingMetricSource(data, name) {
    if (!data || typeof data !== "object") {
        return undefined;
    }

    /*
     * Backend metadata ita nian uza:
     * precision_macro
     * recall_macro
     *
     * Aliases sira-ne'e permite frontend lee kampu
     * ne'ebé nia naran mak precision/recall ka *_macro.
     */
    const aliases = {
        accuracy: [
            "accuracy"
        ],
        precision: [
            "precision_macro",
            "precision"
        ],
        recall: [
            "recall_macro",
            "recall"
        ],
        f1_macro: [
            "f1_macro",
            "f1"
        ]
    };

    const keys = aliases[name] || [name];

    for (const key of keys) {
        if (
            data[key] !== undefined &&
            data[key] !== null
        ) {
            return data[key];
        }

        if (
            data.metrics &&
            typeof data.metrics === "object" &&
            data.metrics[key] !== undefined &&
            data.metrics[key] !== null
        ) {
            return data.metrics[key];
        }
    }

    return undefined;
}

function trainingGetCount(data, keys) {
    for (const key of keys) {
        if (trainingIsNumber(data[key])) {
            return Number(data[key]);
        }
    }

    return undefined;
}

function trainingGetVersion(data) {
    return (
        data.version ??
        data.model_version ??
        data.meta?.version ??
        "N/A"
    );
}

/* =========================================================
   3. TRAINING CONFIGURATION
========================================================= */

function getTrainingConfig() {
    const testInput = trainingEl("testSize");
    const depthInput = trainingEl("maxDepth");
    const splitInput = trainingEl("minSplit");

    if (!testInput || !depthInput || !splitInput) {
        throw new Error(
            "Input training la kompletu. Verifika training.html."
        );
    }

    const testText = testInput.value.trim();
    const depthText = depthInput.value.trim();
    const splitText = splitInput.value.trim();

    if (!testText) {
        throw new Error("Test Size tenke iha valor.");
    }

    const testSize = Number(testText);

    if (
        !Number.isFinite(testSize) ||
        testSize < 0.05 ||
        testSize > 0.95
    ) {
        throw new Error(
            "Test Size tenke entre 0.05 no 0.95."
        );
    }

    if (!splitText) {
        throw new Error(
            "Min Samples Split tenke iha valor."
        );
    }

    const minSplit = Number(splitText);

    if (
        !Number.isSafeInteger(minSplit) ||
        minSplit < 2
    ) {
        throw new Error(
            "Min Samples Split tenke númeru inteiru 2 ka liu."
        );
    }

    let maxDepth = null;

    if (depthText !== "") {
        maxDepth = Number(depthText);

        if (
            !Number.isSafeInteger(maxDepth) ||
            maxDepth < 1
        ) {
            throw new Error(
                "Max Depth tenke númeru inteiru pozitivu ka mamuk."
            );
        }
    }

    return {
        test_size: testSize,
        max_depth: maxDepth,
        min_samples_split: minSplit,
        random_state: 42
    };
}

/* =========================================================
   4. CONFUSION MATRIX
========================================================= */

function trainingNormalizeMatrix(data) {
    if (!data || typeof data !== "object") {
        return null;
    }

    const classes = Array.isArray(data.classes)
        ? data.classes.map(value => String(value))
        : [];

    const matrix = Array.isArray(data.confusion_matrix)
        ? data.confusion_matrix
        : [];

    if (
        classes.length === 0 ||
        matrix.length !== classes.length
    ) {
        return null;
    }

    const valid = matrix.every(row =>
        Array.isArray(row) &&
        row.length === classes.length &&
        row.every(value =>
            trainingIsNumber(value) &&
            Number(value) >= 0
        )
    );

    if (!valid) return null;

    return {
        classes,
        matrix: matrix.map(row => row.map(Number))
    };
}

function trainingRenderMatrix(matrixData) {
    if (!matrixData) {
        return trainingEmpty(
            "Confusion matrix la disponivel iha resposta backend."
        );
    }

    const { classes, matrix } = matrixData;
    const maxValue = Math.max(1, ...matrix.flat());

    const headers = classes.map(name => `
        <th scope="col">${trainingEscape(name)}</th>
    `).join("");

    const rows = matrix.map((row, rowIndex) => {
        const cells = row.map((value, columnIndex) => {
            const intensity = value / maxValue;
            const opacity = (0.08 + intensity * 0.55).toFixed(3);
            const isCorrect = rowIndex === columnIndex;

            return `
                <td
                    title="Actual: ${trainingEscape(classes[rowIndex])}; Predicted: ${trainingEscape(classes[columnIndex])}; Count: ${value}"
                    style="
                        background-color: rgba(37, 99, 235, ${opacity});
                        ${isCorrect ? "outline:1px solid rgba(37,99,235,.25);" : ""}
                    "
                >
                    ${trainingEscape(trainingNumber(value))}
                </td>
            `;
        }).join("");

        return `
            <tr>
                <th scope="row">
                    ${trainingEscape(classes[rowIndex])}
                </th>
                ${cells}
            </tr>
        `;
    }).join("");

    return `
        <div class="training-matrix-wrap">
            <table class="training-matrix">
                <thead>
                    <tr>
                        <th class="matrix-corner" scope="col">
                            Actual ↓ / Predicted →
                        </th>
                        ${headers}
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>

        <div class="training-legend">
            Kontajen aas liu hatudu kor nakukun liu.
            Diagonal mak predisaun ne'ebé hanesan ho label real.
            Kontajen hotu mai husi backend.
        </div>
    `;
}

/* =========================================================
   5. CHARTS
========================================================= */

function trainingRenderCharts(data, matrixData) {
    trainingDestroyCharts();

    const metricsCanvas = trainingEl("trainingMetricsChart");
    const distributionCanvas = trainingEl(
        "trainingDistributionChart"
    );

    if (typeof Chart === "undefined") {
        if (metricsCanvas) {
            metricsCanvas.parentElement.innerHTML = trainingEmpty(
                "Chart.js la karrega. Verifika internet no CDN."
            );
        }

        if (distributionCanvas) {
            distributionCanvas.parentElement.innerHTML = trainingEmpty(
                "Chart.js la karrega. Verifika internet no CDN."
            );
        }

        return;
    }

    /* Gráfiku métrika */
    if (metricsCanvas) {
        const metricNames = [
            ["accuracy", "Accuracy"],
            ["precision", "Precision Macro"],
            ["recall", "Recall Macro"],
            ["f1_macro", "F1 Macro"]
        ];

        const availableMetrics = metricNames
            .map(([key, label]) => ({
                label,
                value: trainingMetricSource(data, key)
            }))
            .filter(item =>
                trainingIsNumber(item.value) &&
                Number(item.value) >= 0 &&
                Number(item.value) <= 1
            );

        if (availableMetrics.length > 0) {
            trainingMetricChart = new Chart(metricsCanvas, {
                type: "bar",
                data: {
                    labels: availableMetrics.map(item => item.label),
                    datasets: [{
                        label: "Score (%)",
                        data: availableMetrics.map(
                            item => Number(item.value) * 100
                        ),
                        backgroundColor: [
                            "#2563eb",
                            "#0d9488",
                            "#d97706",
                            "#7c3aed"
                        ],
                        borderRadius: 7,
                        maxBarThickness: 55
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: context =>
                                    `${context.parsed.y.toFixed(2)}%`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            min: 0,
                            max: 100,
                            ticks: {
                                callback: value => `${value}%`
                            }
                        }
                    }
                }
            });
        } else {
            metricsCanvas.parentElement.innerHTML = trainingEmpty(
                "Backend seidauk fó métrika ne'ebé bele dezenha."
            );
        }
    }

    /* Distribuisaun klase real iha test set */
    if (distributionCanvas) {
        if (matrixData) {
            const { classes, matrix } = matrixData;

            const classCounts = matrix.map(row =>
                row.reduce((sum, value) => sum + value, 0)
            );

            trainingDistributionChart = new Chart(
                distributionCanvas,
                {
                    type: "bar",
                    data: {
                        labels: classes,
                        datasets: [{
                            label: "Amostra teste",
                            data: classCounts,
                            backgroundColor: [
                                "#dc2626",
                                "#64748b",
                                "#16a34a",
                                "#2563eb",
                                "#9333ea"
                            ],
                            borderRadius: 7,
                            maxBarThickness: 65
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    precision: 0
                                }
                            }
                        }
                    }
                }
            );
        } else {
            distributionCanvas.parentElement.innerHTML = trainingEmpty(
                "La bele kalkula distribuisaun klase tanba confusion matrix la disponivel."
            );
        }
    }
}

/* =========================================================
   6. RENDER TRAINING RESULT
========================================================= */

function trainingRenderResult(data) {
    const resultBox = trainingEl("result");
    const versionBox = trainingEl("resultVersion");

    if (!resultBox) return;

    trainingDestroyCharts();

    const matrixData = trainingNormalizeMatrix(data);

    const accuracy = trainingMetricSource(data, "accuracy");
    const precision = trainingMetricSource(data, "precision");
    const recall = trainingMetricSource(data, "recall");
    const f1Macro = trainingMetricSource(data, "f1_macro");

    const nSamples = trainingGetCount(data, [
        "n_samples",
        "total_samples"
    ]);

    const nClasses = trainingGetCount(data, [
        "n_classes"
    ]);

    const nTrain = trainingGetCount(data, [
        "n_train",
        "n_train_samples",
        "training_samples"
    ]);

    const nTest = trainingGetCount(data, [
        "n_test",
        "n_test_samples",
        "testing_samples"
    ]);

    const featureCount = trainingGetCount(data, [
        "feature_count"
    ]);

    const version = trainingGetVersion(data);

    if (versionBox) {
        versionBox.textContent = `Versaun: ${version}`;
    }

    const metricCards = [
        trainingRenderKpi(
            "Total Sampel",
            trainingNumber(nSamples),
            "Amostra validu ne'ebé uza"
        ),
        trainingRenderKpi(
            "Jumlah Kelas",
            trainingNumber(nClasses),
            "Klase sentimentu"
        ),
        trainingRenderKpi(
            "Accuracy",
            trainingPercent(accuracy),
            "Proporsaun predisaun loos"
        ),
        trainingRenderKpi(
            "Precision Macro",
            trainingPercent(precision),
            "Média precision entre klase"
        ),
        trainingRenderKpi(
            "Recall Macro",
            trainingPercent(recall),
            "Média recall entre klase"
        ),
        trainingRenderKpi(
            "F1 Macro",
            trainingPercent(f1Macro),
            "Média F1 entre klase"
        ),
        trainingRenderKpi(
            "Data Treinamentu",
            trainingNumber(nTrain),
            "Amostra ba aprendizagem"
        ),
        trainingRenderKpi(
            "Data Teste",
            trainingNumber(nTest),
            "Amostra ba avaliasaun"
        ),
        trainingRenderKpi(
            "TF-IDF Features",
            trainingNumber(featureCount),
            "Feature ne'ebé modelu uza"
        )
    ].join("");

    resultBox.innerHTML = `
        <div class="training-kpis">
            ${metricCards}
        </div>

        <div class="training-heading">
            <h3>Evaluasaun Modelu</h3>
        </div>

        <p class="small">
            Resultadu ne'e bazeia ba resposta treinamentu husi backend.
            Métrika ne'ebé la disponivel sei hatudu N/A.
        </p>

        <div class="training-charts">
            <div class="training-chart-box">
                <h3>Métrika Modelu</h3>
                <p>Komparasaun Accuracy, Precision, Recall no F1 Macro.</p>

                <div class="training-chart-canvas">
                    <canvas
                        id="trainingMetricsChart"
                        aria-label="Gráfiku métrika modelu"
                        role="img"
                    ></canvas>
                </div>
            </div>

            <div class="training-chart-box">
                <h3>Distribuisaun Sentimentu</h3>
                <p>
                    Kontajen label real iha data teste, kalkula husi
                    liña confusion matrix; la'ós dataset tomak.
                </p>

                <div class="training-chart-canvas">
                    <canvas
                        id="trainingDistributionChart"
                        aria-label="Distribuisaun sentimentu iha data teste"
                        role="img"
                    ></canvas>
                </div>
            </div>
        </div>

        <div class="training-section-gap">
            <h3>Confusion Matrix</h3>
            <p class="small">
                Liña mak label real; koluna mak label ne'ebé modelu prediz.
            </p>
            ${trainingRenderMatrix(matrixData)}
        </div>
    `;

    trainingRenderCharts(data, matrixData);
    trainingSetModelBadge(true, "Rezultadu disponivel");
}

/* =========================================================
   7. MODEL METADATA
========================================================= */

function trainingRenderMetadata(meta) {
    const metadataBox = trainingEl("metadata");
    if (!metadataBox) return;

    let jsonText;

    try {
        jsonText = JSON.stringify(meta ?? {}, null, 2);
    } catch {
        jsonText = "Metadata la bele konverte ba JSON.";
    }

    metadataBox.innerHTML = `
        <pre class="training-meta">${trainingEscape(jsonText)}</pre>
    `;
}

/* =========================================================
   8. TRAIN MODEL
========================================================= */

async function train() {
    const btnTrain = trainingEl("btnTrain");
    const btnStatus = trainingEl("btnStatus");
    const resultBox = trainingEl("result");

    if (btnTrain && btnTrain.disabled) return;

    let config;

    try {
        config = getTrainingConfig();
    } catch (error) {
        trainingAlert(error.message, "warning");
        return;
    }

    const originalText = btnTrain
        ? btnTrain.textContent
        : "Latih Model";

    if (btnTrain) {
        btnTrain.disabled = true;
        btnTrain.textContent = "Treina hela...";
    }

    if (btnStatus) btnStatus.disabled = true;

    trainingAlert(
        "Treinamentu hahú ona. Favór hein to'o prosesu remata.",
        "info"
    );

    trainingSetModelBadge(false, "Treinamentu hela");

    if (resultBox) {
        trainingDestroyCharts();
        resultBox.innerHTML = trainingEmpty(
            "Backend prosesu dataset, treina modelu no kalkula métrika."
        );
    }

    try {
        const response = await api("/training/train", {
            method: "POST",
            body: JSON.stringify(config)
        });

        if (!response || typeof response !== "object") {
            throw new Error(
                "Resposta backend la iha formatu JSON ne'ebé espera."
            );
        }

        if (response.trained === false) {
            throw new Error(
                response.message ||
                response.detail ||
                "Backend informa katak modelu seidauk treinu."
            );
        }

        /*
         * Endpoint train ita nian fó metrics iha raiz JSON.
         * Se resposta iha envelope result, suporta envelope ne'e mos.
         */
        const resultData =
            response.result &&
            typeof response.result === "object"
                ? response.result
                : response;

        trainingRenderResult(resultData);
        trainingRenderMetadata(
            response.meta ??
            resultData.meta ??
            response
        );

        trainingClearAlert();

        trainingAlert(
            "Treinamentu remata. Dashboard atualiza ho rezultadu backend.",
            "ok"
        );
    } catch (error) {
        trainingSetModelBadge(false, "Treinamentu falla");

        trainingAlert(
            error.message || "Treinamentu modelu falla.",
            "err"
        );

        if (resultBox) {
            trainingDestroyCharts();
            resultBox.innerHTML = trainingEmpty(
                "La konsege kompleta treinamentu. Verifika resposta API, dataset ho label, no log backend."
            );
        }
    } finally {
        if (btnTrain) {
            btnTrain.disabled = false;
            btnTrain.textContent = originalText;
        }

        if (btnStatus) btnStatus.disabled = false;
    }
}

/* =========================================================
   9. CHECK MODEL STATUS
========================================================= */

async function checkTrainingStatus() {
    const btnStatus = trainingEl("btnStatus");
    const btnTrain = trainingEl("btnTrain");

    if (btnStatus && btnStatus.disabled) return;

    const originalText = btnStatus
        ? btnStatus.textContent
        : "Periksa Status";

    if (btnStatus) {
        btnStatus.disabled = true;
        btnStatus.textContent = "Verifika hela...";
    }

    if (btnTrain) btnTrain.disabled = true;

    try {
        const response = await api("/training/status", {
            method: "GET"
        });

        if (!response || typeof response !== "object") {
            throw new Error(
                "Resposta status backend la validu."
            );
        }

        const ready = response.ready === true;

        /*
         * Status response iha metadata diretamente iha raiz
         * ka iha propriedade meta, depende ba backend.
         */
        const meta =
            response.meta &&
            typeof response.meta === "object"
                ? response.meta
                : response;

        trainingRenderMetadata(meta);

        trainingSetModelBadge(
            ready,
            ready ? "Modelu prontu" : "Modelu seidauk prontu"
        );

        const hasMatrix =
            trainingNormalizeMatrix(meta) !== null;

        const hasMetric = [
            "accuracy",
            "precision",
            "recall",
            "f1_macro"
        ].some(key =>
            trainingMetricSource(meta, key) !== undefined
        );

        if (ready && (hasMatrix || hasMetric)) {
            trainingRenderResult(meta);
        } else {
            const resultBox = trainingEl("result");

            if (resultBox) {
                trainingDestroyCharts();

                resultBox.innerHTML = trainingEmpty(
                    ready
                        ? "Modelu prontu. Status API la fó métrika evaluasaun ka confusion matrix."
                        : "Modelu seidauk prontu. Klik Latih Model atu treina."
                );
            }

            const versionBox = trainingEl("resultVersion");

            if (versionBox) {
                versionBox.textContent =
                    `Versaun: ${trainingGetVersion(meta)}`;
            }
        }

        trainingClearAlert();

        trainingAlert(
            ready
                ? "Status backend: modelu prontu atu uza."
                : "Status backend: modelu seidauk prontu.",
            ready ? "ok" : "warning"
        );
    } catch (error) {
        trainingAlert(
            error.message || "La konsege lee status modelu.",
            "err"
        );

        trainingSetModelBadge(false, "Status la disponivel");
    } finally {
        if (btnStatus) {
            btnStatus.disabled = false;
            btnStatus.textContent = originalText;
        }

        if (btnTrain) btnTrain.disabled = false;
    }
}

/* Compatibilidade ho kódigu antigu */
async function status() {
    return checkTrainingStatus();
}

/* =========================================================
   10. INITIALIZE
========================================================= */

function initTraining() {
    if (trainingInitialized) return;

    trainingInitialized = true;

    const btnTrain = trainingEl("btnTrain");
    const btnStatus = trainingEl("btnStatus");

    if (btnTrain) {
        btnTrain.addEventListener("click", train);
    }

    if (btnStatus) {
        btnStatus.addEventListener("click", checkTrainingStatus);
    }
}
