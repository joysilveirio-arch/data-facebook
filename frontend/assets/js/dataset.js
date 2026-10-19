
"use strict";

/* ============================================================
   DATASET MANAGEMENT
   Backend: FastAPI /api/v1
   Dependencies: api.js
   ============================================================ */

let _page = 1;
let _size = 20;
let _loadingRecords = false;
let _datasetInitialized = false;

/* ============================================================
   INITIALIZATION
   ============================================================ */

function initDataset() {
    if (_datasetInitialized) return;
    _datasetInitialized = true;

    const btnImport = el("btnImport");
    const btnSearch = el("btnSearch");
    const searchInput = el("q");
    const labelFilter = el("fLabel");

    if (btnImport) {
        btnImport.addEventListener("click", doImport);
    }

    if (btnSearch) {
        btnSearch.addEventListener("click", () => {
            _page = 1;
            loadRecords();
        });
    }

    if (searchInput) {
        searchInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                _page = 1;
                loadRecords();
            }
        });
    }

    if (labelFilter) {
        labelFilter.addEventListener("change", () => {
            _page = 1;
            loadRecords();
        });
    }

    initRecordForm();
    loadRecords();
}

/* ============================================================
   ALERTS
   ============================================================ */

function datasetAlert(message, type = "info") {
    const target = el("alert");
    if (!target) return;

    const allowedTypes = ["ok", "err", "info", "warning"];
    const safeType = allowedTypes.includes(type) ? type : "info";

    target.innerHTML = `
        <div class="alert ${safeType}" role="alert">
            ${esc(message)}
        </div>
    `;
}

function clearDatasetAlert() {
    const target = el("alert");
    if (target) target.replaceChildren();
}

/* ============================================================
   IMPORT DATASET
   ============================================================ */

async function doImport() {
    const button = el("btnImport");
    const pathInput = el("filePath");
    const formatInput = el("format");
    const resetInput = el("reset");

    if (!button || !pathInput || !formatInput || !resetInput) {
        datasetAlert(
            "Kontrola HTML: btnImport, filePath, format no reset tenke iha.",
            "err"
        );
        return;
    }

    const filePath = pathInput.value.trim();

    if (!filePath) {
        datasetAlert("Favor hatama file path ba dataset.", "warning");
        pathInput.focus();
        return;
    }

    if (filePath.includes("\0")) {
        datasetAlert("File path inválidu.", "warning");
        return;
    }

    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = "Importando...";
    clearDatasetAlert();

    try {
        const result = await api("/datasets/import", {
            method: "POST",
            body: JSON.stringify({
                file_path: filePath,
                format: formatInput.value,
                reset: resetInput.checked
            })
        });

        const imported = Number(result?.imported ?? 0);
        const skipped = Number(result?.skipped ?? 0);
        const total = Number(result?.total_now ?? 0);

        datasetAlert(
            `Importasaun remata. Importadu: ${imported}; ` +
            `skip: ${skipped}; total: ${total}.`,
            "ok"
        );

        _page = 1;
        await loadRecords();

    } catch (error) {
        datasetAlert(
            error.message || "Import dataset la konsege.",
            "err"
        );
    } finally {
        button.disabled = false;
        button.textContent = originalText || "Import Dataset";
    }
}

/* ============================================================
   CREATE / UPDATE FORM
   ============================================================ */

function initRecordForm() {
    const form = el("recordForm");
    const cancelButton = el("btnCancelEdit");
    const clearButton = el("btnClearForm");

    if (form) {
        form.addEventListener("submit", saveRecord);
    }

    if (cancelButton) {
        cancelButton.addEventListener("click", resetRecordForm);
    }

    if (clearButton) {
        clearButton.addEventListener("click", resetRecordForm);
    }

    resetRecordForm();
}

function resetRecordForm() {
    const form = el("recordForm");

    if (form) form.reset();

    const defaults = {
        recordId: "",
        likesCount: "0"
    };

    Object.entries(defaults).forEach(([id, value]) => {
        const field = el(id);
        if (field) field.value = value;
    });

    const title = el("recordFormTitle");
    if (title) title.textContent = "Tambah Record";

    const saveButton = el("btnSaveRecord");
    if (saveButton) saveButton.textContent = "Guardar Record";

    const cancelButton = el("btnCancelEdit");
    if (cancelButton) cancelButton.style.display = "none";

    clearDatasetAlert();
}

function inputValue(id) {
    const input = el(id);
    return input ? input.value.trim() : "";
}

/* ============================================================
   SAVE RECORD
   ============================================================ */

async function saveRecord(event) {
    event.preventDefault();

    const saveButton = el("btnSaveRecord");
    const recordId = inputValue("recordId");

    const commentId = inputValue("commentId");
    const text = inputValue("recordText");
    const likesRaw = inputValue("likesCount");

    if (!commentId) {
        datasetAlert("Comment ID tenke prienxe.", "warning");
        el("commentId")?.focus();
        return;
    }

    if (!text) {
        datasetAlert("Texto tenke prienxe.", "warning");
        el("recordText")?.focus();
        return;
    }

    const likesCount = likesRaw === "" ? 0 : Number(likesRaw);

    if (!Number.isSafeInteger(likesCount) || likesCount < 0) {
        datasetAlert(
            "Likes tenke númeru inteiru ne'ebé la negativu.",
            "warning"
        );
        el("likesCount")?.focus();
        return;
    }

    const payload = {
        comment_id: commentId,
        text,
        author_name: inputValue("authorName") || null,
        author_id: inputValue("authorId") || null,
        post_title: inputValue("postTitle") || null,
        date: inputValue("recordDate") || null,
        likes_count: likesCount,
        source_url: inputValue("sourceUrl") || null
    };

    Object.keys(payload).forEach(key => {
        if (payload[key] === null) delete payload[key];
    });

    const originalText = saveButton?.textContent || "Guardar Record";

    if (saveButton) {
        saveButton.disabled = true;
        saveButton.textContent = recordId
            ? "Atualizando..."
            : "Guardando...";
    }

    clearDatasetAlert();

    try {
        if (recordId) {
            await api(`/records/${encodeURIComponent(recordId)}`, {
                method: "PUT",
                body: JSON.stringify(payload)
            });

            datasetAlert("Record atualiza ho susesu.", "ok");
        } else {
            await api("/records/", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            datasetAlert("Record foun kria ho susesu.", "ok");
        }

        resetRecordForm();
        _page = 1;
        await loadRecords();

    } catch (error) {
        datasetAlert(
            error.message || "La konsege rai record.",
            "err"
        );
    } finally {
        if (saveButton) {
            saveButton.disabled = false;

            saveButton.textContent = inputValue("recordId")
                ? "Atualiza Record"
                : originalText;
        }
    }
}

/* ============================================================
   EDIT RECORD
   ============================================================ */

async function editRecord(id) {
    const recordId = Number(id);

    if (!Number.isSafeInteger(recordId) || recordId <= 0) {
        datasetAlert("ID record inválidu.", "err");
        return;
    }

    clearDatasetAlert();

    try {
        const record = await api(
            `/records/${encodeURIComponent(recordId)}`
        );

        if (!record || typeof record !== "object") {
            throw new Error("Backend la fó record válidu.");
        }

        const fields = {
            recordId: record.id,
            commentId: record.comment_id,
            recordText: record.text,
            authorName: record.author_name,
            authorId: record.author_id,
            postTitle: record.post_title,
            recordDate: record.date,
            likesCount: record.likes_count ?? 0,
            sourceUrl: record.source_url
        };

        Object.entries(fields).forEach(([id, value]) => {
            const input = el(id);
            if (input) input.value = value ?? "";
        });

        const title = el("recordFormTitle");
        if (title) title.textContent = `Edit Record ID ${record.id}`;

        const saveButton = el("btnSaveRecord");
        if (saveButton) saveButton.textContent = "Atualiza Record";

        const cancelButton = el("btnCancelEdit");
        if (cancelButton) cancelButton.style.display = "";

        el("recordForm")?.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        datasetAlert(`Record ID ${record.id} prontu atu edita.`, "info");

    } catch (error) {
        datasetAlert(
            error.message || "La konsege lee record atu edita.",
            "err"
        );
    }
}

/* ============================================================
   LOAD RECORDS
   Expected response:
   {
       "items": [],
       "total": 0
   }
   ============================================================ */

async function loadRecords() {
    if (_loadingRecords) return;

    const rows = el("rows");

    if (!rows) {
        datasetAlert("La hetan tabela tbody ho ID rows.", "err");
        return;
    }

    _loadingRecords = true;

    rows.innerHTML = `
        <tr>
            <td colspan="7" style="text-align:center;padding:24px;">
                Karrega dadus...
            </td>
        </tr>
    `;

    try {
        const query = inputValue("q");
        const labelElement = el("fLabel");
        const label = labelElement ? labelElement.value.trim() : "";

        const params = new URLSearchParams({
            page: String(_page),
            page_size: String(_size)
        });

        if (query) params.set("q", query);
        if (label) params.set("label", label);

        const data = await api(`/records/?${params.toString()}`);

        const items = Array.isArray(data?.items) ? data.items : [];
        const total = Math.max(0, Number(data?.total) || 0);
        const totalPages = Math.max(1, Math.ceil(total / _size));

        if (_page > totalPages) {
            _page = totalPages;
            _loadingRecords = false;
            return await loadRecords();
        }

        if (items.length === 0) {
            rows.innerHTML = `
                <tr>
                    <td colspan="7"
                        style="text-align:center;padding:30px;">
                        Dadus la iha. Import dataset ka kria record foun.
                    </td>
                </tr>
            `;
        } else {
            rows.innerHTML = items.map(record => {
                const id = Number(record.id);

                const validId =
                    Number.isSafeInteger(id) && id > 0;

                const safeId = validId ? id : null;
                const commentId = record.comment_id ?? "";
                const recordText = record.text ?? "";
                const author = record.author_name ?? "N/A";

                const actions = validId
                    ? `
                        <div style="display:flex;gap:6px;flex-wrap:wrap;">
                            <button type="button"
                                class="btn ghost"
                                data-edit-id="${safeId}">
                                Edit
                            </button>
                            <button type="button"
                                class="btn ghost danger"
                                data-delete-id="${safeId}">
                                Hapus
                            </button>
                        </div>
                    `
                    : "ID inválidu";

                return `
                    <tr>
                        <td>${safeId ?? "—"}</td>
                        <td title="${esc(commentId)}">
                            ${esc(truncate(commentId, 35))}
                        </td>
                        <td title="${esc(recordText)}">
                            ${esc(truncate(recordText, 80))}
                        </td>
                        <td>${esc(author)}</td>
                        <td>${badge(record.label)}</td>
                        <td>${badge(record.predicted_label)}</td>
                        <td>${actions}</td>
                    </tr>
                `;
            }).join("");

            rows.querySelectorAll("[data-edit-id]").forEach(button => {
                button.addEventListener("click", () => {
                    editRecord(button.dataset.editId);
                });
            });

            rows.querySelectorAll("[data-delete-id]").forEach(button => {
                button.addEventListener("click", () => {
                    delRec(button.dataset.deleteId);
                });
            });
        }

        renderPager(total, totalPages);

    } catch (error) {
        rows.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center;padding:24px;">
                    La konsege karrega dadus.
                </td>
            </tr>
        `;

        datasetAlert(
            error.message || "Erro bainhira lee dataset.",
            "err"
        );
    } finally {
        _loadingRecords = false;
    }
}

/* ============================================================
   PAGINATION
   ============================================================ */

function renderPager(total, totalPages) {
    const pager = el("pager");
    if (!pager) return;

    pager.innerHTML = `
        <button type="button"
            class="btn ghost"
            id="btnPrevPage"
            ${_page <= 1 ? "disabled" : ""}>
            « Anterior
        </button>

        <span class="small" style="padding:0 10px;align-self:center;">
            Página ${_page} husi ${totalPages}
            (${formatNumber(total)} dadus)
        </span>

        <button type="button"
            class="btn ghost"
            id="btnNextPage"
            ${_page >= totalPages ? "disabled" : ""}>
            Próximo »
        </button>
    `;

    el("btnPrevPage")?.addEventListener("click", () => {
        if (!_loadingRecords && _page > 1) {
            _page--;
            loadRecords();
        }
    });

    el("btnNextPage")?.addEventListener("click", () => {
        if (!_loadingRecords && _page < totalPages) {
            _page++;
            loadRecords();
        }
    });
}

/* ============================================================
   DELETE RECORD
   ============================================================ */

async function delRec(id) {
    const recordId = Number(id);

    if (!Number.isSafeInteger(recordId) || recordId <= 0) {
        datasetAlert("ID record inválidu.", "err");
        return;
    }

    if (!confirm(
        `Ita hakarak hamoos record ID ${recordId} permanentemente?`
    )) {
        return;
    }

    clearDatasetAlert();

    try {
        await api(`/records/${encodeURIComponent(recordId)}`, {
            method: "DELETE"
        });

        datasetAlert(`Record ID ${recordId} hamoos ho susesu.`, "ok");

        await loadRecords();

    } catch (error) {
        datasetAlert(
            error.message || "La konsege hamoos record.",
            "err"
        );
    }
}

/* ============================================================
   AUTO INITIALIZATION
   ============================================================ */

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDataset, {
        once: true
    });
} else {
    initDataset();
}
