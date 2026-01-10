document.addEventListener("DOMContentLoaded", () => {
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") {
        console.error("ALL_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    let CATEGORY_TYPES = [];
    let ACCOUNTS = [];

    const categoriesRequiringDestination = [
        "savings",
        "investment",
        "debt",
        "transfer",
        "retirement"
    ];

    // -------------------------
    // LOAD CATEGORIES & ACCOUNTS
    // -------------------------
    function loadCategories() {
        if (typeof CATEGORIES_API_URL === "undefined") return Promise.resolve();
        return fetch(CATEGORIES_API_URL, { credentials: "same-origin" })
            .then(res => res.ok ? res.json() : Promise.reject("Failed to load categories"))
            .then(data => { CATEGORY_TYPES = data.category_types || []; });
    }

    function loadAccounts() {
        if (typeof ACCOUNTS_API_URL === "undefined") return Promise.resolve();
        return fetch(ACCOUNTS_API_URL, { credentials: "same-origin" })
            .then(res => res.ok ? res.json() : Promise.reject("Failed to load accounts"))
            .then(data => { ACCOUNTS = data.accounts || []; });
    }

    // -------------------------
    // BUILD SELECT DROPDOWNS
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

    function buildDestinationSelect(tx) {
        const td = document.createElement("td");
        td.className = "destination-cell";
        td.style.display = "none";

        const select = document.createElement("select");
        select.className = "form-select form-select-sm account-select";
        select.id = `accountchoice_${tx.id}`;
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

    function updateDestinationHeaderVisibility() {
        const header = document.getElementById("destinationHeader");
        if (!header) return;
        const hasVisible = Array.from(document.querySelectorAll(".destination-cell"))
            .some(td => td.style.display !== "none");
        header.style.display = hasVisible ? "" : "none";
    }

    // -------------------------
    // RENDER TRANSACTIONS
    // -------------------------
    function renderAllTransactions(transactions, appliedFilters = [], oneAccount = false) {
        const tbody = document.getElementById("allTransactionsBody");
        const theadRow = document.getElementById("allTransactionsHeader");
        if (!tbody || !theadRow) return;
        tbody.innerHTML = "";

        // Handle running balance header
        if (oneAccount && !document.getElementById("runningBalanceHeader")) {
            const th = document.createElement("th");
            th.id = "runningBalanceHeader";
            th.textContent = "Running Balance";
            theadRow.appendChild(th);
        } else if (!oneAccount && document.getElementById("runningBalanceHeader")) {
            document.getElementById("runningBalanceHeader").remove();
        }

        if (!transactions.length) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No transactions found.</td></tr>`;
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
                <td class="category-cell"></td>
                <td class="category-dropdown-cell"></td>
                <td class="text-truncate" style="max-width:400px;" title="${tx.note || ""}">${tx.note || ""}</td>
                <td>${tx.account_display}</td>
                <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
                ${oneAccount ? `<td class="text-end fw-semibold text-white">$${tx.running_balance}</td>` : ""}
            `;

            // Append type/category dropdowns
            tr.querySelector(".category-cell").appendChild(buildTypeSelect(tx));
            tr.querySelector(".category-dropdown-cell").appendChild(buildCategorySelect(tx, tx.type_name));
            tr.appendChild(buildDestinationSelect(tx));

            fragment.appendChild(tr);
        });

        tbody.appendChild(fragment);

        // Render applied filters
        const filtersContainer = document.getElementById("appliedFiltersContainer");
        if (filtersContainer) {
            filtersContainer.innerHTML = "";
            if (appliedFilters.length) {
                appliedFilters.forEach(filter => {
                    const span = document.createElement("span");
                    span.className = "badge bg-primary text-white me-1";
                    span.textContent = filter;
                    filtersContainer.appendChild(span);
                });
            } else {
                const span = document.createElement("span");
                span.className = "text-muted";
                span.textContent = "No filters applied";
                filtersContainer.appendChild(span);
            }
        }
    }

    // -------------------------
    // EVENT DELEGATION FOR TYPE/CATEGORY CHANGES
    // -------------------------
    document.addEventListener("change", function(e) {
        const target = e.target;
        if (target.classList.contains("type-select")) {
            const tr = target.closest("tr");
            const txId = target.dataset.transactionId;
            const categoryTd = tr.querySelector(".category-dropdown-cell");
            const accountSelect = document.getElementById(`accountchoice_${txId}`);
            const destCell = accountSelect?.closest(".destination-cell");

            if (!target.value) {
                categoryTd.innerHTML = "";
                categoryTd.appendChild(buildCategorySelect({id: txId, category_name: ""}, null));
                if (destCell) { destCell.style.display = "none"; accountSelect.value = ""; accountSelect.style.display = "none"; }
                updateDestinationHeaderVisibility();
                return;
            }

            const newCategorySelect = buildCategorySelect({id: txId, category_name: ""}, target.value);
            categoryTd.innerHTML = "";
            categoryTd.appendChild(newCategorySelect);
            newCategorySelect.style.display = "inline-block";
        }

        if (target.classList.contains("category-select")) {
            const txId = target.dataset.transactionId;
            const selectedOption = target.options[target.selectedIndex];
            const categoryType = (selectedOption.dataset.categorytype || "").toLowerCase();
            const accountSelect = document.getElementById(`accountchoice_${txId}`);
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
    // INITIAL LOAD
    // -------------------------
    Promise.all([loadCategories(), loadAccounts()])
        .then(() => fetch(ALL_TRANSACTIONS_API_URL, { credentials: "same-origin" }))
        .then(res => res.ok ? res.json() : Promise.reject(`HTTP ${res.status}`))
        .then(data => renderAllTransactions(data.transactions || [], data.appliedfilters || [], data.one_account))
        .catch(err => console.error("Transaction load failed:", err));

});
