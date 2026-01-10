document.addEventListener("DOMContentLoaded", () => {
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") {
        console.error("ALL_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    // Example: fetch these once from your API or hardcode
    let types = [], categories = [], accounts = [];

    fetch("/api/transaction-metadata/") // returns {types: [...], categories: [...], accounts: [...]}
        .then(res => res.json())
        .then(data => {
            types = data.types;
            categories = data.categories;
            accounts = data.accounts;
        });

    const filterForm = document.getElementById("filterTransactionsForm");
    filterForm.addEventListener("submit", e => {
        e.preventDefault();
        const formData = new FormData(filterForm);

        fetch(ALL_TRANSACTIONS_API_URL, {
            method: "POST",
            credentials: "same-origin",
            headers: { "X-CSRFToken": formData.get("csrfmiddlewaretoken") },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            renderAllTransactions(data.transactions || [], data.appliedfilters || [], data.one_account, types, categories, accounts);
            const filterModalEl = document.getElementById("filterModalTransactions");
            const filterModal = bootstrap.Modal.getInstance(filterModalEl);
            if (filterModal) filterModal.hide();
        })
        .catch(err => console.error("Transaction load failed:", err));
    });

    const tbody = document.getElementById("allTransactionsBody");

    fetch(ALL_TRANSACTIONS_API_URL, { credentials: "same-origin" })
        .then(res => res.json())
        .then(data => {
            renderAllTransactions(data.transactions || [], data.appliedfilters || [], data.one_account, types, categories, accounts);
        })
        .catch(err => {
            console.error("Transaction load failed:", err);
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger py-4">Failed to load transactions.</td></tr>`;
            }
        });

    function renderAllTransactions(transactions, appliedFilters = [], oneAccount = false, types = [], categories = [], accounts = []) {
        const tbody = document.getElementById("allTransactionsBody");
        const theadRow = document.getElementById("allTransactionsHeader");
        if (!tbody || !theadRow) return;

        tbody.innerHTML = "";

        // Add/remove running balance header
        if (oneAccount && !document.getElementById("runningBalanceHeader")) {
            const th = document.createElement("th");
            th.id = "runningBalanceHeader";
            th.textContent = "Running Balance";
            theadRow.appendChild(th);
        } else if (!oneAccount && document.getElementById("runningBalanceHeader")) {
            document.getElementById("runningBalanceHeader").remove();
        }

        if (!transactions.length) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">No transactions found.</td></tr>`;
            return;
        }

        const fragment = document.createDocumentFragment();

        transactions.forEach(tx => {
            const tr = document.createElement("tr");
            tr.classList.add("transaction-row");

            const typeOptions = types.map(t => `<option value="${t.id}" ${t.name === tx.type_name ? "selected" : ""}>${t.name}</option>`).join("");
            const categoryOptions = categories.map(c => `<option value="${c.id}" ${c.name === tx.category_name ? "selected" : ""}>${c.name}</option>`).join("");
            const accountOptions = accounts.map(a => `<option value="${a.id}" ${a.name === tx.account_display ? "selected" : ""}>${a.name}</option>`).join("");

            tr.innerHTML = `
                <td class="editcol" hidden>
                    <input class="form-check-input" type="checkbox" name="selectedtransactions" value="${tx.id}">
                </td>
                <td><input type="month" class="form-control form-control-sm editable" data-field="date" value="${tx.date}"></td>
                <td><select class="form-select form-select-sm editable" data-field="type">${typeOptions}</select></td>
                <td><select class="form-select form-select-sm editable" data-field="category">${categoryOptions}</select></td>
                <td contenteditable="true" class="editable" data-field="note">${tx.note || ""}</td>
                <td><select class="form-select form-select-sm editable" data-field="account">${accountOptions}</select></td>
                <td contenteditable="true" class="editable text-end" data-field="amount">${tx.amount}</td>
                ${oneAccount ? `<td class="text-end fw-semibold text-white" readonly>${tx.running_balance}</td>` : ""}
            `;

            fragment.appendChild(tr);
        });

        tbody.appendChild(fragment);

        // Attach blur/change events for inline saving
        tbody.querySelectorAll(".editable").forEach(cell => {
            cell.addEventListener(cell.tagName === "SELECT" ? "change" : "blur", e => {
                const target = e.target;
                const tr = target.closest("tr");
                const txId = tr.querySelector('input[name="selectedtransactions"]').value;
                let value = target.value;
                if (target.dataset.field === "amount") value = value.replace(/\$/g,"").trim();
                updateTransaction(txId, target.dataset.field, value);
            });
        });

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

    function updateTransaction(txId, field, value) {
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        fetch(`/api/transactions/${txId}/`, {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": csrfToken,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ [field]: value })
        })
        .then(res => res.json())
        .then(data => console.log("Updated", data))
        .catch(err => console.error("Update failed:", err));
    }
});
