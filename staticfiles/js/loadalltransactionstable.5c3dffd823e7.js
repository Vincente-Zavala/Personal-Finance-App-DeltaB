document.addEventListener("DOMContentLoaded", () => {
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") return console.error("ALL_TRANSACTIONS_API_URL is not defined!");

    let CATEGORY_TYPES = [];
    let ACCOUNTS = [];
    const categoriesRequiringDestination = ["savings","investment","debt","transfer","retirement"];
    let editMode = false;

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
    // BUILD DROPDOWNS
    // -------------------------
    function buildTypeSelect(tx) {
        const select = document.createElement("select");
        select.className = "form-select form-select-sm type-select d-none"; // hidden by default
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
        select.className = "form-select form-select-sm category-select d-none"; // hidden by default
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
        select.className = "form-select form-select-sm account-select d-none"; // hidden by default
        select.id = `accountchoice_${tx.id}`;
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
                <td class="type-cell">
                    <span class="tx-display">${tx.type_name}</span>
                </td>
                <td class="category-cell">
                    <span class="tx-display">${tx.category_name || ""}</span>
                </td>
                <td class="text-truncate" style="max-width:400px;" title="${tx.note || ""}">
                    <span class="tx-display">${tx.note || ""}</span>
                    <input type="text" class="form-control form-control-sm text-end tx-input d-none" value="${tx.note || ""}">
                </td>
                <td>${tx.account_display}</td>
                <td class="text-end fw-semibold text-primary">
                    <span class="tx-display">$${tx.amount}</span>
                    <input type="number" class="form-control form-control-sm text-end tx-input d-none" value="${tx.amount}">
                </td>
            `;

            // Add dropdowns (hidden by default)
            tr.querySelector(".type-cell").appendChild(buildTypeSelect(tx));
            tr.querySelector(".category-cell").appendChild(buildCategorySelect(tx, tx.type_name));
            tr.appendChild(buildDestinationSelect(tx));

            fragment.appendChild(tr);
        });

        tbody.appendChild(fragment);
    }

    // -------------------------
    // TOGGLE EDIT MODE
    // -------------------------
    const toggleEditBtn = document.getElementById("toggleEdit");
    toggleEditBtn.addEventListener("click", () => {
        editMode = !editMode;

        document.querySelectorAll(".transaction-row").forEach(tr => {
            // Show/hide dropdowns for type/category
            const typeSelect = tr.querySelector(".type-select");
            const categorySelect = tr.querySelector(".category-select");
            const typeSpan = tr.querySelector(".type-cell .tx-display");
            const categorySpan = tr.querySelector(".category-cell .tx-display");

            if (editMode) {
                typeSelect.classList.remove("d-none");
                categorySelect.classList.remove("d-none");
                typeSpan.classList.add("d-none");
                categorySpan.classList.add("d-none");
            } else {
                typeSelect.classList.add("d-none");
                categorySelect.classList.add("d-none");
                typeSpan.classList.remove("d-none");
                categorySpan.classList.remove("d-none");
            }

            // Show/hide other inputs (notes, amounts)
            tr.querySelectorAll(".tx-input").forEach(input => {
                input.classList.toggle("d-none", !editMode);
                const span = input.previousElementSibling;
                if(span && span.classList.contains("tx-display")) {
                    span.classList.toggle("d-none", editMode);
                }
            });
        });

        document.getElementById("submittransactions").style.display = editMode ? "inline-block" : "none";
    });

    // -------------------------
    // HANDLE DROPDOWN CHANGES
    // -------------------------
    document.addEventListener("change", e => {
        const target = e.target;
        if (target.classList.contains("type-select")) {
            const tr = target.closest("tr");
            const txId = target.dataset.transactionId;
            const categoryTd = tr.querySelector(".category-cell");
            const accountSelect = document.getElementById(`accountchoice_${txId}`);
            const destCell = accountSelect?.closest(".destination-cell");

            if (!target.value) {
                categoryTd.querySelector(".category-select").style.display = "none";
                if (destCell) { destCell.style.display = "none"; accountSelect.value = ""; accountSelect.style.display = "none"; }
                updateDestinationHeaderVisibility();
                return;
            }

            const newCategorySelect = buildCategorySelect({id: txId, category_name: ""}, target.value);
            categoryTd.innerHTML = "";
            categoryTd.appendChild(categoryTd.querySelector(".tx-display"));
            categoryTd.appendChild(newCategorySelect);
            if(editMode) newCategorySelect.classList.remove("d-none");
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
                accountSelect.style.display = editMode ? "inline-block" : "none";
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
