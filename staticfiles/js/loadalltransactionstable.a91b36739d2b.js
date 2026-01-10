// -------------------------
// GLOBAL CACHE
// -------------------------
let CATEGORY_TYPES = [];
let ACCOUNTS = [];

// Categories that require a destination account
const categoriesRequiringDestination = ["savings", "investment", "debt", "transfer", "retirement"];

// -------------------------
// LOAD CATEGORIES
// -------------------------
function loadCategories() {
    if (!CATEGORIES_API_URL) {
        console.error("CATEGORIES_API_URL is not defined!");
        return Promise.resolve();
    }

    return fetch(CATEGORIES_API_URL, { credentials: "same-origin" })
        .then(res => {
            if (!res.ok) throw new Error("Failed to load categories");
            return res.json();
        })
        .then(data => { CATEGORY_TYPES = data.category_types || []; });
}

// -------------------------
// LOAD ACCOUNTS
// -------------------------
function loadAccounts() {
    if (!ACCOUNTS_API_URL) {
        console.error("ACCOUNTS_API_URL is not defined!");
        return Promise.resolve();
    }

    return fetch(ACCOUNTS_API_URL, { credentials: "same-origin" })
        .then(res => {
            if (!res.ok) throw new Error("Failed to load accounts");
            return res.json();
        })
        .then(data => { ACCOUNTS = data.accounts || []; });
}

// -------------------------
// BUILD TYPE SELECT
// -------------------------
function buildTypeSelect(tx) {
    const select = document.createElement("select");
    select.className = "form-select form-select-sm type-select";
    select.dataset.transactionId = tx.id;
    select.innerHTML = `<option value="">Select Type...</option>`;

    CATEGORY_TYPES.forEach(ct => {
        const option = document.createElement("option");
        option.value = ct.name;
        option.textContent = ct.name;
        if (ct.name === tx.type_name) option.selected = true;
        select.appendChild(option);
    });

    return select;
}

// -------------------------
// BUILD CATEGORY SELECT
// -------------------------
function buildCategorySelect(tx, selectedType = null) {
    const select = document.createElement("select");
    select.className = "form-select form-select-sm category-select";
    select.dataset.transactionId = tx.id;
    select.style.display = selectedType ? "" : "none";
    select.innerHTML = `<option value="">Select Category...</option>`;

    CATEGORY_TYPES.forEach(ct => {
        if (!selectedType || ct.name.toLowerCase() !== selectedType.toLowerCase()) return;
        ct.categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat.id;
            option.textContent = cat.name;
            option.dataset.categorytype = ct.type;
            if (cat.name === tx.category_name) option.selected = true;
            select.appendChild(option);
        });
    });

    return select;
}

// -------------------------
// BUILD DESTINATION ACCOUNT SELECT
// -------------------------
function buildDestinationSelect(tx) {
    const td = document.createElement("td");
    td.className = "destination-cell";
    td.style.display = "none";

    const select = document.createElement("select");
    select.className = "form-select form-select-sm account-select";
    select.id = `accountchoice_${tx.id}`;
    select.name = `accountchoice_${tx.id}`;
    select.style.display = "none";
    select.innerHTML = `<option value="">Select Destination Account</option>`;

    ACCOUNTS.forEach(acct => {
        const option = document.createElement("option");
        option.value = acct.id;
        option.textContent = acct.name;
        select.appendChild(option);
    });

    td.appendChild(select);
    return td;
}

// -------------------------
// UPDATE DESTINATION HEADER VISIBILITY
// -------------------------
function updateDestinationHeaderVisibility() {
    const header = document.getElementById("destinationHeader");
    if (!header) return;
    const hasVisible = Array.from(document.querySelectorAll(".destination-cell"))
        .some(cell => cell.style.display !== "none");
    header.style.display = hasVisible ? "" : "none";
}

// -------------------------
// RENDER PENDING TRANSACTIONS
// -------------------------
function renderPendingTransactions(transactions) {
    const tbody = document.getElementById("pendingTransactionsBody");
    const container = document.getElementById("pendingTransactionsContainer");
    if (!tbody) return;

    tbody.innerHTML = "";
    container.style.display = "block";
    if (!transactions?.length) { container.style.display = "none"; return; }

    const fragment = document.createDocumentFragment();

    transactions.forEach(tx => {
        const tr = document.createElement("tr");
        tr.classList.add("transaction-row");
        tr.dataset.type = tx.type_name;

        // Basic columns
        tr.innerHTML = `
            <td class="editcol" hidden>
                <input class="form-check-input" type="checkbox" name="selectedtransactions" value="${tx.id}">
            </td>
            <td>${tx.formatted_date}</td>
            <td class="text-truncate" style="max-width:400px;" title="${tx.note}">${tx.note}</td>
            <td>${tx.account_display}</td>
            <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
        `;

        // TYPE COLUMN
        const typeTd = document.createElement("td");
        typeTd.appendChild(buildTypeSelect(tx));
        tr.appendChild(typeTd);

        // CATEGORY COLUMN
        const categoryTd = document.createElement("td");
        categoryTd.appendChild(buildCategorySelect(tx, tx.type_name));
        tr.appendChild(categoryTd);

        // DESTINATION ACCOUNT COLUMN
        const destTd = buildDestinationSelect(tx);
        tr.appendChild(destTd);

        fragment.appendChild(tr);
    });

    tbody.appendChild(fragment);
    updateDestinationHeaderVisibility();
}

// -------------------------
// EVENT DELEGATION FOR TYPE/CATEGORY CHANGES
// -------------------------
document.addEventListener("change", function(e) {
    const target = e.target;

    // Type changed → update category dropdown & hide/show destination account
    if (target.classList.contains("type-select")) {
        const tr = target.closest("tr");
        const transactionId = target.dataset.transactionId;
        const categoryTd = tr.querySelector(".category-select").parentElement;
        const accountSelect = document.getElementById(`accountchoice_${transactionId}`);
        const destCell = accountSelect?.closest(".destination-cell");

        // No type selected → hide category & destination
        if (!target.value) {
            categoryTd.innerHTML = "";
            categoryTd.appendChild(buildCategorySelect({id: transactionId, category_name: ""}, null));
            if (destCell) { destCell.style.display = "none"; accountSelect.value = ""; accountSelect.style.display = "none"; }
            updateDestinationHeaderVisibility();
            return;
        }

        // Type selected → rebuild category dropdown
        const newCategorySelect = buildCategorySelect({id: transactionId, category_name: ""}, target.value);
        categoryTd.innerHTML = "";
        categoryTd.appendChild(newCategorySelect);
        newCategorySelect.style.display = "inline-block";
        updateDestinationHeaderVisibility();
        return;
    }

    // Category changed → show/hide destination account
    if (target.classList.contains("category-select")) {
        const transactionId = target.dataset.transactionId;
        const selectedOption = target.options[target.selectedIndex];
        const categoryType = (selectedOption.dataset.categorytype || "").toLowerCase();
        const accountSelect = document.getElementById(`accountchoice_${transactionId}`);
        const destCell = accountSelect?.closest(".destination-cell");

        if (!accountSelect || !destCell) return;

        if (categoriesRequiringDestination.includes(categoryType)) {
            destCell.style.display = "";
            accountSelect.style.display = "inline-block";
        } else {
            destCell.style.display = "none";
            accountSelect.style.display = "none";
            accountSelect.value = "";
        }

        updateDestinationHeaderVisibility();
    }
});

// -------------------------
// DOM READY
// -------------------------
document.addEventListener("DOMContentLoaded", () => {
    if (!PENDING_TRANSACTIONS_API_URL) {
        console.error("PENDING_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    Promise.all([loadCategories(), loadAccounts(),
        fetch(PENDING_TRANSACTIONS_API_URL, { credentials: "same-origin" })
            .then(res => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
    ])
    .then(([_, __, data]) => renderPendingTransactions(data.transactions))
    .catch(err => console.error("Transaction load failed:", err));
});
