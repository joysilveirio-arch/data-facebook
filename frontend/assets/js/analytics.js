
/* =========================================================
   FACEBOOK SENTIMENT ANALYTICS
   File: frontend/assets/js/analytics.js

   Requires:
   - Chart.js
   - frontend/assets/js/api.js
   - HTML IDs: alert, cards, c1, c2, c3

   API:
   GET /api/v1/analytics/overview
   ========================================================= */

"use strict";

/* =========================================================
   CHART INSTANCE STORAGE
   ========================================================= */

const analyticsCharts = Object.create(null);

/* =========================================================
   DOM HELPERS
   ========================================================= */

function analyticsElement(id) {
    if (typeof el === "function") {
        const element = el(id);
        if (element) return element;
    }

    return document.getElementById(id);
}

function analyticsNumber(value, decimals = 0) {
    if (
        value === null ||
        value === undefined ||
        value === "" ||
        !Number.isFinite(Number(value))
    ) {
        return "0";
    }

    return Number(value).toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function analyticsSetMessage(message, type = "info") {
    const alertBox = analyticsElement("alert");

    if (!alertBox) return;

    alertBox.replaceChildren();

    if (!message) return;

    const box = document.createElement("div");

    box.className =
        type === "error" ? "alert err" : "alert";

    box.textContent = message;
    alertBox.appendChild(box);
}

/* =========================================================
   API RESPONSE NORMALIZATION
   ========================================================= */

function analyticsNormalizeResponse(response) {
    let result = response;

    for (let i = 0; i < 5; i++) {
        if (
            !result ||
            typeof result !== "object" ||
            Array.isArray(result)
        ) {
            break;
        }

        if (
            result.data &&
            typeof result.data === "object" &&
            !Array.isArray(result.data)
        ) {
            result = result.data;
            continue;
        }

        if (
            result.result &&
            typeof result.result === "object" &&
            !Array.isArray(result.result)
        ) {
            result = result.result;
            continue;
        }

        break;
    }

    if (
        !result ||
        typeof result !== "object" ||
        Array.isArray(result)
    ) {
        throw new Error(
            "Resposta API analytics la válidu."
        );
    }

    return result;
}

function analyticsFirstValue(data, keys, fallback = null) {
    for (const key of keys) {
        if (
            Object.prototype.hasOwnProperty.call(data, key) &&
            data[key] !== null &&
            data[key] !== undefined
        ) {
            return data[key];
        }
    }

    return fallback;
}

function analyticsNormalizeDistribution(value) {
    const result = {};

    if (Array.isArray(value)) {
        value.forEach(item => {
            if (!item || typeof item !== "object") return;

            const label =
                item.label ??
                item.sentiment ??
                item.name;

            const count =
                item.count ??
                item.total ??
                item.value;

            if (
                label !== undefined &&
                count !== undefined &&
                Number.isFinite(Number(count))
            ) {
                result[String(label)] = Number(count);
            }
        });

        return result;
    }

    if (!value || typeof value !== "object") {
        return result;
    }

    Object.entries(value).forEach(([label, count]) => {
        if (
            count !== null &&
            count !== "" &&
            Number.isFinite(Number(count))
        ) {
            result[label] = Number(count);
        }
    });

    return result;
}

/* =========================================================
   CHART HELPERS
   ========================================================= */

function destroyAnalyticsChart(id) {
    if (analyticsCharts[id]) {
        analyticsCharts[id].destroy();
        delete analyticsCharts[id];
    }

    const canvas = analyticsElement(id);

    if (
        canvas &&
        typeof Chart !== "undefined" &&
        typeof Chart.getChart === "function"
    ) {
        const existing = Chart.getChart(canvas);

        if (existing) {
            existing.destroy();
        }
    }
}

function createAnalyticsChart(id, config) {
    const canvas = analyticsElement(id);

    if (!canvas) {
        console.warn(
            `Canvas "${id}" la hetan iha HTML.`
        );
        return null;
    }

    if (typeof Chart === "undefined") {
        throw new Error("Chart.js seidauk karrega.");
    }

    destroyAnalyticsChart(id);

    analyticsCharts[id] = new Chart(canvas, config);

    return analyticsCharts[id];
}

function analyticsChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                position: "bottom",
                labels: {
                    color: "#bac8df",
                    padding: 18,
                    usePointStyle: true,
                    pointStyle: "circle",
                    font: {
                        family: "system-ui",
                        size: 12
                    }
                }
            },

            tooltip: {
                backgroundColor: "#101a2e",
                titleColor: "#ffffff",
                bodyColor: "#edf3ff",
                borderColor: "#334563",
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8
            }
        },

        animation: {
            duration: 500
        }
    };
}

function analyticsCartesianOptions() {
    return {
        ...analyticsChartOptions(),

        scales: {
            x: {
                ticks: {
                    color: "#96a8c8",
                    maxRotation: 45,
                    minRotation: 0
                },

                grid: {
                    color: "rgba(51, 69, 99, 0.35)"
                }
            },

            y: {
                beginAtZero: true,

                ticks: {
                    color: "#96a8c8",
                    precision: 0
                },

                grid: {
                    color: "rgba(51, 69, 99, 0.35)"
                }
            }
        }
    };
}

function analyticsEmptyChart(id, message) {
    const canvas = analyticsElement(id);

    if (!canvas) return;

    destroyAnalyticsChart(id);

    const parent = canvas.parentElement;

    if (!parent) return;

    let empty = parent.querySelector(
        `[data-empty-chart="${id}"]`
    );

    if (!empty) {
        empty = document.createElement("div");
        empty.dataset.emptyChart = id;
        empty.className = "empty-state";

        parent.appendChild(empty);
    }

    empty.textContent = message;
    canvas.style.display = "none";
}

function analyticsShowChart(id) {
    const canvas = analyticsElement(id);

    if (!canvas) return;

    canvas.style.display = "block";

    const parent = canvas.parentElement;

    if (parent) {
        const empty = parent.querySelector(
            `[data-empty-chart="${id}"]`
        );

        if (empty) {
            empty.remove();
        }
    }
}

/* =========================================================
   KPI CARDS
   ========================================================= */

function analyticsRenderKpis(data) {
    const cards = analyticsElement("cards");

    if (!cards) return;

    const totalRecords = analyticsFirstValue(
        data,
        [
            "total_records",
            "total_posts",
            "total",
            "total_comments"
        ],
        null
    );

    const totalLabeled = analyticsFirstValue(
        data,
        [
            "total_labeled",
            "labeled_records",
            "total_labels"
        ],
        null
    );

    const totalPredicted = analyticsFirstValue(
        data,
        [
            "total_predicted",
            "predicted_records",
            "total_predictions"
        ],
        null
    );

    const avgLikes = analyticsFirstValue(
        data,
        [
            "avg_likes",
            "average_likes",
            "mean_likes"
        ],
        null
    );

    const items = [
        {
            title: "Total Record",
            value: totalRecords,
            description: "Total dadus iha sistema"
        },
        {
            title: "Berlabel Manual",
            value: totalLabeled,
            description: "Dadus ho label manual"
        },
        {
            title: "Sudah Diprediksi",
            value: totalPredicted,
            description: "Dadus ne'ebé modelu analiza ona"
        },
        {
            title: "Rata-rata Like",
            value: avgLikes,
            decimals: 2,
            description: "Média like ba record"
        }
    ];

    cards.replaceChildren();

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "card";

        const heading = document.createElement("h3");
        heading.textContent = item.title;

        const value = document.createElement("div");
        value.className = "value";

        value.textContent =
            item.value === null
                ? "N/A"
                : analyticsNumber(
                    item.value,
                    item.decimals || 0
                );

        const description = document.createElement("div");
        description.className = "small";
        description.textContent = item.description;

        card.append(heading, value, description);
        cards.appendChild(card);
    });
}

/* =========================================================
   SENTIMENT DISTRIBUTION
   ========================================================= */

function analyticsSentimentColor(label, index) {
    const key = String(label)
        .toLowerCase()
        .trim();

    const colors = {
        positive: "#34d399",
        negative: "#fb7185",
        neutral: "#94a3b8",

        positif: "#34d399",
        negatif: "#fb7185",
        netral: "#94a3b8",

        positivu: "#34d399",
        negativu: "#fb7185",
        neutru: "#94a3b8"
    };

    const palette = [
        "#4f8cff",
        "#a78bfa",
        "#fbbf24",
        "#67e8f9"
    ];

    return colors[key] || palette[index % palette.length];
}

function analyticsRenderDistribution(
    id,
    rawDistribution,
    type
) {
    const distribution =
        analyticsNormalizeDistribution(rawDistribution);

    const entries = Object.entries(distribution).filter(
        ([, value]) =>
            Number.isFinite(value) && value > 0
    );

    /*
     * Jangan lukis pie/doughnut apabila semua nilai sifar.
     * Paparkan mesej yang menerangkan keadaan sebenar data.
     */
    if (entries.length === 0) {
        analyticsEmptyChart(
            id,
            "Seidauk iha dadus sentimentu. Halo label manual ka predisaun uluk."
        );
        return;
    }

    analyticsShowChart(id);

    createAnalyticsChart(id, {
        type,

        data: {
            labels: entries.map(([label]) => label),

            datasets: [{
                data: entries.map(([, count]) => count),

                backgroundColor: entries.map(
                    ([label], index) =>
                        analyticsSentimentColor(label, index)
                ),

                borderColor: "#101a2e",
                borderWidth: 3,
                hoverOffset: 8
            }]
        },

        options: {
            ...analyticsChartOptions(),

            cutout:
                type === "doughnut"
                    ? "66%"
                    : undefined
        }
    });
}

/* =========================================================
   ACTIVITY BY DATE
   API field: daily_counts
   Example: [{date: "2026-10-13T14:37:09.000Z", count: 1}]
   ========================================================= */

function analyticsGetActivityRows(data) {
    const raw = analyticsFirstValue(
        data,
        [
            "daily_counts",
            "activity",
            "daily_activity",
            "date_activity",
            "activity_by_date"
        ],
        []
    );

    if (!Array.isArray(raw)) return [];

    const grouped = {};

    raw.forEach(item => {
        if (!item || typeof item !== "object") return;

        const rawDate =
            item.date ??
            item.day ??
            item.created_date ??
            item.period;

        const count =
            item.count ??
            item.total ??
            item.total_records ??
            item.records ??
            item.value;

        if (
            rawDate === undefined ||
            count === undefined ||
            !Number.isFinite(Number(count))
        ) {
            return;
        }

        const parsedDate = new Date(rawDate);

        if (Number.isNaN(parsedDate.getTime())) return;

        // Group timestamps by UTC calendar day.
        const day = parsedDate.toISOString().slice(0, 10);

        grouped[day] =
            (grouped[day] || 0) + Number(count);
    });

    return Object.entries(grouped)
        .map(([date, count]) => ({ date, count }))
        .sort((a, b) => a.date.localeCompare(b.date));
}

function analyticsRenderActivity(data) {
    const rows = analyticsGetActivityRows(data);

    if (rows.length === 0) {
        analyticsEmptyChart(
            "c3",
            "API seidauk fó dadus atividade tuir data."
        );
        return;
    }

    analyticsShowChart("c3");

    createAnalyticsChart("c3", {
        type: "line",

        data: {
            labels: rows.map(item => item.date),

            datasets: [{
                label: "Total Dadus",
                data: rows.map(item => item.count),

                borderColor: "#4f8cff",
                backgroundColor: "rgba(79, 140, 255, 0.18)",
                pointBackgroundColor: "#76a5ff",

                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.3
            }]
        },

        options: {
            ...analyticsCartesianOptions(),

            interaction: {
                intersect: false,
                mode: "index"
            }
        }
    });
}

/* =========================================================
   MAIN INITIALIZER
   ========================================================= */

async function initAnalytics() {
    analyticsSetMessage("");

    if (typeof Chart === "undefined") {
        analyticsSetMessage(
            "Chart.js seidauk karrega. Verifika koneksaun internet no script Chart.js.",
            "error"
        );
        return;
    }

    if (typeof api !== "function") {
        analyticsSetMessage(
            "Funksaun api() la hetan. Verifika assets/js/api.js.",
            "error"
        );
        return;
    }

    try {
        const response = await api("/analytics/overview");
        const data = analyticsNormalizeResponse(response);

        console.info("Analytics API response:", data);

        analyticsRenderKpis(data);

        const manualDistribution = analyticsFirstValue(
            data,
            [
                "distribution_label",
                "label_distribution",
                "manual_label_distribution",
                "distribution_manual"
            ],
            {}
        );

        const predictedDistribution = analyticsFirstValue(
            data,
            [
                "distribution_predicted",
                "predicted_distribution",
                "sentiment_distribution",
                "prediction_distribution"
            ],
            {}
        );

        analyticsRenderDistribution(
            "c1",
            manualDistribution,
            "pie"
        );

        analyticsRenderDistribution(
            "c2",
            predictedDistribution,
            "doughnut"
        );

        analyticsRenderActivity(data);

        analyticsSetMessage("");

    } catch (error) {
        console.error("Analytics error:", error);

        analyticsSetMessage(
            "La konsege carga analytics: " +
            (
                error && error.message
                    ? error.message
                    : "Erro desconhecido."
            ),
            "error"
        );
    }
}
