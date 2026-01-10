// -------------------------
// GLOBAL CACHE
// -------------------------
let CATEGORY_TYPES = [];
let ACCOUNTS = [];

// Categories that require a destination account
const categoriesRequiringDestination = [
    "savings",
    "investment",
    "debt",
    "transfer",
    "retirement"
];

// -------------------------
// LOAD CATEGORIES
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
// LOAD ACCOUNTS
// -------------------------
function loadAccounts() {
    if (typeof ACCOUNTS_API_URL === "undefined") {
        console.error("ACCOUNTS_API_URL is not defined!");
        return Promise.resolve();
    }

    return fetch(ACCOUNTS_API_URL, { credentials: "same-origin" })
        .then(res => {
            if (!res.ok) throw new Error("Failed to load accounts");
            return res.json();
        })
        .then(data => {
            ACCOUNTS = data.accounts || [];
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
            option.dataset.categorytype = ct.type; // used for destination logic

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
// BUILD DESTINATION ACCOUNT SELECT
// -------------------------
function buildDestinationSelect(tx) {
    const td = document.createElement("td");
    td.className = "destination-cell";
    td.style.display = "none"; // hidden by default

    const select = document.createElement("select");
    select.className = "form-select form-select-sm rounded-pill account-select";
    select.id = `accountchoice_${tx.id}`;
    select.name = `accountchoice_${tx.id}`;
    select.style.display = "none";

    select.innerHTML = `<option value="">**Select Destination Account**</option>`;

    ACCOUNTS.forEach(acct => {
        const option = document.createElement("option");
        option.value = acct.id;
        option.textContent = acct.name; // or acct.account_display if available
        select.appendChild(option);
    });

    td.appendChild(select);
    return td;
}

// -------------------------
// UPDATE HEADER VISIBILITY
// -------------------------
function updateDestinationHeaderVisibility() {
    const destinationHeader = document.getElementById("destinationHeader");
    if (!destinationHeader) return;

    const hasVisible = Array.from(document.querySelectorAll(".destination-cell"))
        .some(cell => cell.style.display !== "none");

    destinationHeader.style.display = hasVisible ? "" : "none";
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

        // CATEGORY COLUMN
        const categoryTd = document.createElement("td");
        categoryTd.appendChild(buildCategorySelect(tx));
        tr.appendChild(categoryTd);

        // DESTINATION ACCOUNT COLUMN
        const destinationTd = buildDestinationSelect(tx);
        tr.appendChild(destinationTd);

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
    updateDestinationHeaderVisibility();
}

// -------------------------
// EVENT DELEGATION FOR CATEGORY CHANGE
// -------------------------
document.addEventListener("change", function(e) {
    if (!e.target.classList.contains("category-select")) return;

    const select = e.target;
    const selectedOption = select.options[select.selectedIndex];
    const categoryType = (selectedOption.dataset.categorytype || "").toLowerCase();

    const transactionId = select.dataset.transactionId;
    const accountSelect = document.getElementById(`accountchoice_${transactionId}`);
    const destinationCell = accountSelect?.closest(".destination-cell");

    if (!accountSelect || !destinationCell) return;

    if (categoriesRequiringDestination.includes(categoryType)) {
        destinationCell.style.display = "";
        accountSelect.style.display = "inline-block";
    } else {
        destinationCell.style.display = "none";
        accountSelect.style.display = "none";
        accountSelect.value = "";
    }

    updateDestinationHeaderVisibility();
});

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
        loadAccounts(),
        fetch(PENDING_TRANSACTIONS_API_URL, { credentials: "same-origin" })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
    ])
    .then(([_, __, data]) => {
        renderTransactions(data.transactions);
    })
    .catch(err => {
        console.error("Transaction load failed:", err);
    });
});
