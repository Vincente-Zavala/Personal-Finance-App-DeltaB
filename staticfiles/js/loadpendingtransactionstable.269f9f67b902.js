// -------------------------
// GLOBAL CACHE
// -------------------------
let CATEGORY_TYPES = [];

// -------------------------
// LOAD CATEGORIES ONCE
// -------------------------
function loadCategories() {
    if (typeof CATEGORIES_API_URL === "undefined") {
        console.error("CATEGORIES_API_URL is not defined!");
        return Promise.resolve();
    }

    return fetch(CATEGORIES_API_URL, { credentials: "same-origin" })
        .then(res => {
            if (!res.ok) throw new Error("Failed to load categories");
            return res.json();
        })
        .then(data => {
            CATEGORY_TYPES = data.category_types || [];
        });
}

// -------------------------
// BUILD CATEGORY SELECT
// -------------------------
function buildCategorySelect(tx) {
    const select = document.createElement("select");
    select.className = "form-select form-select-sm rounded-pill category-select";
    select.name = `categorychoice_${tx.id}`;
    select.dataset.transactionId = tx.id;

    select.innerHTML = `<option value="">Select Category...</option>`;

    CATEGORY_TYPES.forEach(ct => {
        const optgroup = document.createElement("optgroup");
        optgroup.label = ct.name;

        ct.categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat.id;
            option.textContent = cat.name;

            // preselect existing category
            if (cat.name === tx.category_name) {
                option.selected = true;
            }

            optgroup.appendChild(option);
        });

        select.appendChild(optgroup);
    });

    return select;
}

// -------------------------
// RENDER TRANSACTIONS
// -------------------------
function renderTransactions(transactions) {
    const tbody = document.getElementById("pendingTransactionsBody");
    const container = document.getElementById("pendingTransactionsContainer");

    if (!tbody) return;

    tbody.innerHTML = "";
    container.style.display = "block";

    if (!transactions || !transactions.length) {
        container.style.display = "none";
        return;
    }

    const fragment = document.createDocumentFragment();

    transactions.forEach(tx => {
        const tr = document.createElement("tr");
        tr.classList.add("transaction-row");
        tr.dataset.type = tx.type_name;

        tr.innerHTML = `
            <td class="editcol" hidden>
                <input class="form-check-input" type="checkbox" name="selectedtransactions" value="${tx.id}">
            </td>
            <td>${tx.formatted_date}</td>
            <td class="text-truncate" style="max-width:400px;" title="${tx.note}">${tx.note}</td>
            <td>${tx.account_display}</td>
            <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
        `;

        // CATEGORY COLUMN
        const categoryTd = document.createElement("td");
        categoryTd.appendChild(buildCategorySelect(tx));
        tr.appendChild(categoryTd);

        // HIDDEN TYPE FIELD
        const hiddenType = document.createElement("input");
        hiddenType.type = "hidden";
        hiddenType.name = `transactiontype_${tx.id}`;
        hiddenType.className = "transaction-type-hidden";
        hiddenType.value = tx.type_name;
        tr.appendChild(hiddenType);

        fragment.appendChild(tr);
    });

    tbody.appendChild(fragment);
}

// -------------------------
// DOM READY
// -------------------------
document.addEventListener("DOMContentLoaded", () => {
    if (typeof PENDING_TRANSACTIONS_API_URL === "undefined") {
        console.error("PENDING_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    Promise.all([
        loadCategories(),
        fetch(PENDING_TRANSACTIONS_API_URL, { credentials: "same-origin" })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
    ])
    .then(([_, data]) => {
        renderTransactions(data.transactions);
    })
    .catch(err => {
        console.error("Transaction load failed:", err);
    });
});
