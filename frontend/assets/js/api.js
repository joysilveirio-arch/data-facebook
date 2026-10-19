
"use strict";

const API = "/api/v1";

async function api(path, opts = {}) {
    const normalizedPath = path.startsWith("/")
        ? path
        : `/${path}`;

    const url = `${API}${normalizedPath}`;

    const headers = {
        Accept: "application/json",
        ...(opts.headers || {})
    };

    const isFormData =
        typeof FormData !== "undefined" &&
        opts.body instanceof FormData;

    if (opts.body != null && !isFormData) {
        const hasContentType = Object.keys(headers).some(
            key => key.toLowerCase() === "content-type"
        );

        if (!hasContentType) {
            headers["Content-Type"] = "application/json";
        }
    }

    let response;

    try {
        response = await fetch(url, {
            ...opts,
            credentials: opts.credentials || "same-origin",
            cache: opts.cache || "no-store",
            headers
        });
    } catch (error) {
        if (error.name === "AbortError") {
            throw error;
        }

        throw new Error(
            `La konsege kontaktu ho backend: ${url}. Verifika servidor API.`
        );
    }

    if (response.status === 204) {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return null;
    }

    const contentType =
        response.headers.get("content-type") || "";

    let data;

    if (contentType.includes("application/json")) {
        try {
            data = await response.json();
        } catch {
            throw new Error(
                `Backend haruka JSON inválidu (HTTP ${response.status}).`
            );
        }
    } else {
        const bodyText = await response.text();
        data = {
            message: bodyText || `HTTP ${response.status}`
        };
    }

    if (!response.ok) {
        const detail =
            data?.detail ??
            data?.message ??
            data?.error ??
            `HTTP ${response.status}`;

        throw new Error(
            typeof detail === "string"
                ? detail
                : JSON.stringify(detail)
        );
    }

    return data;
}

function esc(value) {
    if (value === null || value === undefined) return "";

    return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function el(id) {
    return document.getElementById(id);
}

function badge(label) {
    if (label == null || String(label).trim() === "") {
        return '<span class="badge unlabeled">Unlabeled</span>';
    }

    const original = String(label).trim();
    const normalized = original.toLowerCase();

    const classes = {
        positive: "positive",
        positif: "positive",
        negative: "negative",
        negatif: "negative",
        neutral: "neutral",
        netral: "neutral"
    };

    const cssClass = classes[normalized] || "unlabeled";

    return `<span class="badge ${cssClass}">${esc(original)}</span>`;
}

function truncate(value, maxLength = 80) {
    if (value == null) return "";

    const text = String(value);
    const limit = Math.max(0, Number(maxLength) || 80);

    return text.length > limit
        ? text.slice(0, limit) + "..."
        : text;
}

function showAlert(message, type = "info", targetId = "alert") {
    const target = el(targetId);
    if (!target) return;

    const allowed = ["ok", "err", "warning", "info"];
    const cssClass = allowed.includes(type) ? type : "info";

    target.innerHTML =
        `<div class="alert ${cssClass}">${esc(message)}</div>`;
}

function clearAlert(targetId = "alert") {
    const target = el(targetId);
    if (target) target.innerHTML = "";
}

function formatNumber(value, decimals = 0) {
    if (value == null || value === "") return "—";

    const number = Number(value);
    if (!Number.isFinite(number)) return "—";

    return number.toLocaleString("id-ID", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}
