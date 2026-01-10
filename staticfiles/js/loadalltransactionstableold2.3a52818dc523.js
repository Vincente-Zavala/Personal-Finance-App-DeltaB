document.addEventListener("DOMContentLoaded", () => {
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") {
        console.error("ALL_TRANSACTIONS_API_URL is not defined!");
        return;
    }


    const filterForm = document.getElementById("filterTransactionsForm");
    filterForm.addEventListener("submit", e => {
        e.preventDefault();  // stop default form submit

        const formData = new FormData(filterForm);

        fetch(ALL_TRANSACTIONS_API_URL, {
            method: "POST",
            credentials: "same-origin",
            headers: { "X-CSRFToken": formData.get("csrfmiddlewaretoken") },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            renderAllTransactions(data.transactions || [], data.appliedfilters || [], data.one_account)

            // Close the modal after rendering
            const filterModalEl = document.getElementById("filterModalTransactions"); // your modal id
            const filterModal = bootstrap.Modal.getInstance(filterModalEl); // get modal instance
            if (filterModal) {
                filterModal.hide();
            }
        })
        .catch(err => console.error("Transaction load failed:", err));
    });


    const tbody = document.getElementById("allTransactionsBody");
    const allloadingRow = document.getElementById("allloadingRow");

    fetch(ALL_TRANSACTIONS_API_URL, { credentials: "same-origin" })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (!tbody) {
                console.error("Table body not found!");
                return;
            }

            tbody.innerHTML = ""; // clear loading row

            if (!data.transactions || !data.transactions.length) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-muted py-4">No transactions found.</td>
                    </tr>
                `;
                return;
            }

            const fragment = document.createDocumentFragment();

            data.transactions.forEach(tx => {
                const tr = document.createElement("tr");
                tr.classList.add("transaction-row");
                tr.dataset.type = tx.type_name;

                tr.innerHTML = `
                    <td class="editcol" hidden><input class="form-check-input" type="checkbox" name="selectedtransactions" value="${tx.id}"></td>
                    <td>${tx.formatted_date}</td>
                    <td class="category-cell">${tx.type_name}
                        <span class="tx-display">${tx.type_name}</span>
                        <input type="text" class="form-control form-control-sm text-end tx-input d-none" 
                            name="tx_${tx.id}" value="${tx.type_name}">
                    </td>
                    <td>
                        <span class="tx-display">${tx.category_name}</span>
                        <input type="text" class="form-control form-control-sm text-end tx-input d-none" 
                            name="tx_${tx.id}" value="${tx.category_name}">
                    </td>
                    <td class="text-truncate" style="max-width:400px;">
                        <span class="tx-display">${tx.note}</span>
                        <input type="text" class="form-control form-control-sm text-end tx-input d-none" 
                            name="tx_${tx.id}" value="${tx.note}">
                    </td>
                    <td>${tx.account_display}</td>
                    <td class="text-end fw-semibold text-primary">
                        <span class="tx-display">$${tx.amount}</span>
                        <input type="number" class="form-control form-control-sm text-end tx-input d-none" 
                            name="tx_${tx.id}" value="${tx.amount}">
                    </td>
                `;
                fragment.appendChild(tr);
            });

            tbody.appendChild(fragment);
        })
        .catch(err => {
            console.error("Transaction load failed:", err);
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-danger py-4">
                            Failed to load transactions.
                        </td>
                    </tr>
                `;
            }
        });


    let editMode = false;

    const toggleEditBtn = document.getElementById("toggleEdit");
    toggleEditBtn.addEventListener("click", () => {
        editMode = !editMode;
    
        document.querySelectorAll(".transaction-row").forEach(tr => {
            // Select all editable inputs and spans inside the row
            const inputs = tr.querySelectorAll(".tx-input");
            const displays = tr.querySelectorAll(".tx-display");
    
            inputs.forEach((input, i) => {
                const display = displays[i]; // match the corresponding span
                if (editMode) {
                    input.classList.remove("d-none");
                    display.classList.add("d-none");
                } else {
                    input.classList.add("d-none");
                    display.classList.remove("d-none");
                    display.textContent = input.value.startsWith("$") ? input.value : `${input.value}`;
                }
            });
        });
    
        document.getElementById("submittransactions").style.display = editMode ? "inline-block" : "none";
    });
        



    // -------------------------
    // RENDER FILTERED TRANSACTIONS
    // -------------------------
    function renderAllTransactions(transactions, appliedFilters = [], oneAccount = false) {

        const tbody = document.getElementById("allTransactionsBody");
        const theadRow = document.getElementById("allTransactionsHeader");
        
        if (!tbody || !theadRow) return;
    
        // Clear table rows
        tbody.innerHTML = "";

        // Add running balance header dynamically
        if (oneAccount && !document.getElementById("runningBalanceHeader")) {
            const th = document.createElement("th");
            th.id = "runningBalanceHeader";
            th.textContent = "Running Balance";
            theadRow.appendChild(th);
        } else if (!oneAccount && document.getElementById("runningBalanceHeader")) {
            // Remove column if not one account
            document.getElementById("runningBalanceHeader").remove();
        }
    
        if (!transactions.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        No transactions found.
                    </td>
                </tr>
            `;
        } else {
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
                    <td class="category-cell">${tx.type_name}</td>
                    <td>${tx.category_name || ""}</td>
                    <td class="text-truncate" style="max-width:400px;" title="${tx.note || ""}">${tx.note || ""}</td>
                    <td>${tx.account_display}</td>
                    <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
                    ${oneAccount ? `<td class="text-end fw-semibold text-white">$${tx.running_balance}</td>` : ""}
                `;
                fragment.appendChild(tr);
            });
    
            tbody.appendChild(fragment);
        }
    
        // Render applied filters
        const filtersContainer = document.getElementById("appliedFiltersContainer");
        if (filtersContainer) {
            filtersContainer.innerHTML = ""; // clear old filters
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
    
    
});
