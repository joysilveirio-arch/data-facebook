
"use strict";

const PAGES = [
    ["index.html", "Dashboard"],
    ["pages/dataset.html", "Dataset"],
    ["pages/preprocessing.html", "Preprocessing"],
    ["pages/labeling.html", "Labeling"],
    ["pages/training.html", "Training"],
    ["pages/prediction.html", "Prediksi"],
    ["pages/analytics.html", "Analitik"],
    ["pages/about.html", "Tentang"],
];

/**
 * Escape text ba HTML.
 * Uza esc() husi api.js se disponivel.
 */
function navEscape(value) {
    if (typeof esc === "function") {
        return esc(value);
    }

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

/**
 * Render sidebar/menu navigasaun.
 *
 * activePage bele simu:
 * "dataset.html"
 * "pages/dataset.html"
 * "Dataset"
 */
function renderNav(activePage = "") {
    const nav = document.getElementById("nav");

    if (!nav) {
        console.warn("Navigation element #nav la hetan.");
        return;
    }

    const pathname = window.location.pathname;
    const isInPagesFolder = /\/pages\/[^/]*$/i.test(pathname);

    const currentFile = decodeURIComponent(
        pathname.split("/").pop() || "index.html"
    ).toLowerCase();

    const activeValue = String(activePage)
        .replace(/\\/g, "/")
        .split("/")
        .pop()
        .toLowerCase();

    nav.innerHTML = PAGES.map(([path, title]) => {
        const fileName = path.split("/").pop().toLowerCase();

        let href;

        if (isInPagesFolder) {
            href = path.startsWith("pages/")
                ? path.replace(/^pages\//, "")
                : "../" + path;
        } else {
            href = path;
        }

        const isActive =
            activeValue === fileName ||
            (!activeValue && currentFile === fileName);

        return `
            <a
                href="${navEscape(href)}"
                class="${isActive ? "active" : ""}"
                ${isActive ? 'aria-current="page"' : ""}
            >
                ${navEscape(title)}
            </a>
        `;
    }).join("");
}
