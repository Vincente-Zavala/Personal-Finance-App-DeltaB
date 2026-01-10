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
// BUILD TYPE SELECT
// -------------------------
function buildTypeSelect(tx) {
    const select = document.createElement("select");
    select.className = "form-select form-select-sm rounded-pill type-select";
    select.name = `typechoice_${tx.id}`;
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
function buildCategorySelect(tx, type = null) {
    const select = document.createElement("select");
    select.className = "form-select form-select-sm rounded-pill category-select";
    select.name = `categorychoice_${tx.id}`;
    select.dataset.transactionId = tx.id;

    // Hide if no type selected
    if (!type) select.style.display = "none";

    select.innerHTML = `<option value="">Select Category...</option>`;

    CATEGORY_TYPES.forEach(ct => {
        if (!type || ct.name.toLowerCase() !== type.toLowerCase()) return; // only include selected type

        ct.categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat.id;
            option.textContent = cat.name;
            option.dataset.categorytype = ct.type;

            if (cat.name === tx.category_name) {
                option.selected = true;
            }

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
    td.style.display = "none"; // hidden by default

    const select = document.createElement("select");
    select.className = "form-select form-select-sm rounded-pill account-select";
    select.id = `accountchoice_${tx.id}`;
    select.name = `accountchoice_${tx.id}`;
    select.style.display = "none";

    select.innerHTML = `<option value="">Select Destination Account**</option>`;

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
function renderPendingTransactions(transactions) {
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

        // TYPE COLUMN
        const typeTd = document.createElement("td");
        typeTd.appendChild(buildTypeSelect(tx));
        tr.appendChild(typeTd);

        // CATEGORY COLUMN (filtered by type)
        const categoryTd = document.createElement("td");
        categoryTd.appendChild(buildCategorySelect(tx, tx.type_name));
        tr.appendChild(categoryTd);

        // DESTINATION ACCOUNT COLUMN
        const destinationTd = buildDestinationSelect(tx);
        tr.appendChild(destinationTd);

        fragment.appendChild(tr);
    });

    tbody.appendChild(fragment);
    updateDestinationHeaderVisibility();
}


// -------------------------
// EVENT DELEGATION FOR CATEGORY CHANGE
// -------------------------
document.addEventListener("change", function(e) {
    const target = e.target;

    if (target.classList.contains("type-select")) {
        const transactionId = target.dataset.transactionId;
        const categoryTd = target.closest("tr").querySelector(".category-select").parentElement;
        const accountSelect = document.getElementById(`accountchoice_${transactionId}`);
        const destinationCell = accountSelect?.closest(".destination-cell");
    
        // If user selects default "Select Type", hide category dropdown AND destination account
        if (!target.value) {
            const hiddenSelect = buildCategorySelect({id: transactionId, category_name: ""}, null);
            categoryTd.innerHTML = "";
            categoryTd.appendChild(hiddenSelect);
    
            if (destinationCell) {
                destinationCell.style.display = "none";
                accountSelect.value = "";
                accountSelect.style.display = "none";
            }
    
            return;
        }
    
        // Build category select only for this type
        const newCategorySelect = buildCategorySelect({id: transactionId, category_name: ""}, target.value);
        categoryTd.innerHTML = "";
        categoryTd.appendChild(newCategorySelect);
    
        // Show the category dropdown
        newCategorySelect.style.display = "inline-block";
        return;
    }
    

    // Category changed → show/hide destination account
    if (target.classList.contains("category-select")) {
        const selectedOption = target.options[target.selectedIndex];
        const categoryType = (selectedOption.dataset.categorytype || "").toLowerCase();
        const transactionId = target.dataset.transactionId;
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
    }
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
        renderPendingTransactions(data.transactions);
    })
    .catch(err => {
        console.error("Transaction load failed:", err);
    });
});
