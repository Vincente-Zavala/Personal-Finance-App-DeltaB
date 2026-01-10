// -------------------------
// GLOBAL CACHE
// -------------------------
import {
    CATEGORY_TYPES,
    ACCOUNTS,
    loadCategories,
    loadAccounts,
    buildTypeSelect,
    buildCategorySelect
} from "./categories_accounts.js";


// Categories that require a destination account
const categoriesRequiringDestination = [
    "savings",
    "investment",
    "debt",
    "transfer",
    "retirement"
];


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

        const typeSelect = buildTypeSelect(tx);
        typeSelect.name = `transactiontype_${tx.id}`;
        typeTd.appendChild(typeSelect);
        tr.appendChild(typeTd);


        // CATEGORY COLUMN (filtered by type)
        const categoryTd = document.createElement("td");

        const categorySelect = buildCategorySelect(tx, tx.type_name)
        categorySelect.name = `categorychoice_${tx.id}`;
        categoryTd.appendChild(categorySelect);
        tr.appendChild(categoryTd);

        // DESTINATION ACCOUNT COLUMN
        const destinationTd = buildDestinationSelect(tx);
        tr.appendChild(destinationTd);

        fragment.appendChild(tr);
    });

    tbody.appendChild(fragment);
    updateDestinationHeaderVisibility();
    updatePendingSubmitVisibility();
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

            updateDestinationHeaderVisibility();
            updatePendingSubmitVisibility();
    
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
        updatePendingSubmitVisibility();
    }


    // Destination set
    // Destination account changed
    if (target.classList.contains("account-select")) {
        updatePendingSubmitVisibility();
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
        loadCategories(),   // shared function
        loadAccounts(),     // shared function
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

