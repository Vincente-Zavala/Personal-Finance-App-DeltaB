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


document.addEventListener("DOMContentLoaded", async () => {
    
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") {
        console.error("ALL_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    try {
        // 🔴 PRELOAD GLOBAL DATA (BLOCKING)
        await Promise.all([
            loadCategories(),
            loadAccounts()
        ]);

        console.log("CATEGORY_TYPES loaded:", CATEGORY_TYPES);
        console.log("ACCOUNTS loaded:", ACCOUNTS);

    } catch (err) {
        console.error("Failed to preload categories/accounts", err);
        return;
    }



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
            renderAllTransactions(data.transactions || [], data.appliedfilters || [], data.one_account)

            const pendingContainer = document.getElementById("pendingTransactionsContainer");
            if (pendingContainer) {
                pendingContainer.style.display = "none";
            }

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
                tr.dataset.editing = "false";


                // Basic columns
                tr.innerHTML = `
                <td class="editcol" hidden>
                    <div class="d-flex align-items-center gap-2">
                        <input 
                            class="form-check-input select-tx" 
                            type="checkbox" 
                            name="selectedtransactions" 
                            value="${tx.id}">
            
                        <button
                            class="btn btn-sm edit-tx p-0"
                            data-tx-id="${tx.id}"
                            type="button">
                            <i class="fa fa-edit text-primary"></i>
                        </button>

                        <button
                            class="btn btn-sm btn-outline-danger tx-cancel p-0 d-none"
                            data-tx-id="${tx.id}"
                            type="button">
                            <i class="fa fa-xmark text-danger"></i>
                        </button>

                        <button
                            class="btn btn-sm btn-outline-primary tx-check p-0 d-none"
                            data-tx-id="${tx.id}"
                            type="button">
                            <i class="fa fa-check text-primary"></i>
                        </button>
                    </div>
                </td>
                `;
            
                // DATE
                // const dateTd = document.createElement("td");
                // dateTd.textContent = tx.formatted_date;


                const dateTd = document.createElement("td");
            
                const dateDisplay = document.createElement("span");
                dateDisplay.className = "tx-display tx-date fw-semibold";
                dateDisplay.textContent = tx.formatted_date;
                
                const dateInput = document.createElement("input");
                dateInput.type = "text"; // ← required for flatpickr
                dateInput.value = tx.date_iso;
                dateInput.className = "form-control form-control-sm tx-input d-none tx-date-input";
                dateInput.name = "date";
                          
            
                dateTd.append(dateDisplay, dateInput);

                tr.appendChild(dateTd);
            
                // TYPE
                const typeTd = document.createElement("td");
            
                const typeDisplay = document.createElement("span");
                typeDisplay.className = "tx-display";
                typeDisplay.textContent = tx.type_name;
            
                const typeSelect = buildTypeSelect(tx);
                typeSelect.classList.add("tx-input", "d-none");
                typeSelect.name = "type";
            
                typeTd.append(typeDisplay, typeSelect);
                tr.appendChild(typeTd);

                // CATEGORY
                const categoryTd = document.createElement("td");
                categoryTd.classList.add("category-col");

                const categoryDisplay = document.createElement("span");
                categoryDisplay.className = "tx-display";
                categoryDisplay.textContent = tx.category_name;

                // store original category ID and name
                categoryTd.dataset.originalCategoryId = String(tx.category_id);
                categoryTd.dataset.originalCategoryName = tx.category_name;

                const categorySelect = buildCategorySelect(tx, tx.type_name);
                categorySelect.classList.add("tx-input", "d-none");
                categorySelect.name = "category";

                const match = Array.from(categorySelect.options)
                .find(o => o.text.trim() === tx.category_name);

                if (match) {
                    categorySelect.value = match.value;
                }


                categoryTd.append(categoryDisplay, categorySelect);
                tr.appendChild(categoryTd);

            
                // NOTE
                const noteTd = document.createElement("td");
            
                const noteDisplay = document.createElement("span");
                noteDisplay.className = "tx-display";
                noteDisplay.textContent = tx.note || "";
            
                const noteInput = document.createElement("input");
                noteInput.type = "text";
                noteInput.value = tx.note || "";
                noteInput.className = "form-control form-control-sm tx-input d-none";
                noteInput.name = "note";
            
                noteTd.append(noteDisplay, noteInput);
                tr.appendChild(noteTd);

                // ACCOUNT
                const accountTd = document.createElement("td");
                accountTd.textContent = tx.account_display || "";
                tr.appendChild(accountTd); 
            
                // AMOUNT
                const amountTd = document.createElement("td");
                amountTd.className = "text-end";
            
                const amountDisplay = document.createElement("span");
                amountDisplay.className = "tx-display fw-semibold text-primary";
                amountDisplay.textContent = `$${tx.amount}`;
            
                const amountInput = document.createElement("input");
                amountInput.type = "number";
                amountInput.value = tx.amount;
                amountInput.className = "form-control form-control-sm text-end tx-input d-none";
                amountInput.name = "amount";
            
                amountTd.append(amountDisplay, amountInput);
                tr.appendChild(amountTd);

            
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

document.addEventListener("click", (e) => {
    const editBtn = e.target.closest(".edit-tx");
    const cancelBtn = e.target.closest(".tx-cancel");
    const saveBtn = e.target.closest(".tx-check");

    // ---- EDIT BUTTON CLICK ----
    if (editBtn) {
        const row = editBtn.closest(".transaction-row");
        if (!row) return;

        const inputs = row.querySelectorAll(".tx-input");
        const displays = row.querySelectorAll(".tx-display");
        const buttons = row.querySelectorAll(".tx-cancel, .tx-check");
        const editButton = row.querySelector(".edit-tx");

        // Close any other row in edit mode
        document.querySelectorAll(".transaction-row").forEach(r => {
            if (r !== row && r.dataset.editing === "true") {
                r.querySelectorAll(".tx-input").forEach(i => i.classList.add("d-none"));
                r.querySelectorAll(".tx-display").forEach(d => d.classList.remove("d-none"));
                r.querySelectorAll(".tx-cancel, .tx-check").forEach(b => b.classList.add("d-none"));
                r.querySelector(".edit-tx")?.classList.remove("d-none");
                r.dataset.editing = "false";
            }
        });

        // Enter edit mode
        inputs.forEach(i => i.classList.remove("d-none"));
        displays.forEach(d => d.classList.add("d-none"));
        buttons.forEach(b => b.classList.remove("d-none"));
        if (editButton) editButton.classList.add("d-none");

        // Store original values
        inputs.forEach(input => input.dataset.originalValue = input.value);

        const typeSelect = row.querySelector('select[name="type"]');
        const categoryTd = row.querySelector('.category-col');
        const categorySelect = categoryTd.querySelector('select[name="category"]');
        const categoryDisplay = categoryTd.querySelector('.tx-display');

        row.dataset.originalType = typeSelect.value;
        row.dataset.originalCategoryId = categorySelect.value;
        row.dataset.originalCategoryName = categoryDisplay.textContent;

        // ---- TYPE CHANGE HANDLER ----
        typeSelect.addEventListener("change", () => {
            const newType = typeSelect.value;
            const newCategorySelect = buildCategorySelect({ 
                id: categorySelect.dataset.transactionId, 
                category_name: categoryDisplay.textContent 
            }, newType);

            // Replace old category select in DOM
            categoryTd.replaceChild(newCategorySelect, categorySelect);

            // Add back tx-input class for styling
            newCategorySelect.classList.add("tx-input");
        });

    
        const dateInput = row.querySelector('input[name="date"]');
        const dateDisplay = row.querySelector('.tx-date');
        
        if (dateInput && dateDisplay) {
            row.dataset.originalDateValue = dateInput.value;
            row.dataset.originalDateText = dateDisplay.textContent;
        }

        if (dateInput && !dateInput._flatpickr) {
            flatpickr(dateInput, {
                dateFormat: "Y-m-d",      // value sent to backend
                altInput: true,           // pretty display
                altFormat: "M j, Y",      // Jan 5, 2025
                allowInput: true,
                defaultDate: dateInput.value
            });
        }

        
        const amountInput = row.querySelector('input[name="amount"]');
        const amountDisplay = row.querySelector('.tx-display.fw-semibold');

        if (amountInput && amountDisplay) {
            row.dataset.originalAmountValue = amountInput.value; // numeric
            row.dataset.originalAmountText = amountDisplay.textContent; // $ formatted
        }
        

        row.dataset.editing = "true";
        return;
    }

    if (cancelBtn) {
        const row = cancelBtn.closest(".transaction-row");
        if (!row) return;
    
        const inputs = row.querySelectorAll(".tx-input");
        const displays = row.querySelectorAll(".tx-display");
        const buttons = row.querySelectorAll(".tx-cancel, .tx-check");
        const editButton = row.querySelector(".edit-tx");
    
        // --- Restore TYPE ---
        const typeSelect = row.querySelector('select[name="type"]');
        const typeDisplay = row.querySelector('.tx-display');
        if (typeSelect && typeDisplay) {
            typeSelect.value = row.dataset.originalType;
            typeSelect.classList.add("d-none"); // hide input
            typeDisplay.textContent = row.dataset.originalType;
            typeDisplay.classList.remove("d-none"); // show display
        }
    
        // --- Restore CATEGORY ---
        const categoryTd = row.querySelector('.category-col');
        // Remove old select
        const oldSelect = categoryTd.querySelector('select[name^="category"]');
        if (oldSelect) categoryTd.removeChild(oldSelect);
    
        // Rebuild original category select
        const restoredCategorySelect = buildCategorySelect({
            id: oldSelect?.dataset.transactionId || "",
            category_name: row.dataset.originalCategoryName
        }, row.dataset.originalType);
    
        restoredCategorySelect.value = row.dataset.originalCategoryId;
        restoredCategorySelect.classList.add("tx-input", "d-none"); // hide input
        categoryTd.appendChild(restoredCategorySelect);
    
        // Restore display span
        let categoryDisplay = categoryTd.querySelector('.tx-display');
        if (!categoryDisplay) {
            categoryDisplay = document.createElement('span');
            categoryDisplay.className = 'tx-display';
            categoryTd.insertBefore(categoryDisplay, restoredCategorySelect);
        }
        categoryDisplay.textContent = row.dataset.originalCategoryName;
        categoryDisplay.classList.remove("d-none"); // show display
    

        // --- RESTORE AMOUNT ---
        const amountInput = row.querySelector('input[name="amount"]');
        const amountDisplay = row.querySelector('.tx-display.fw-semibold');

        if (amountInput && amountDisplay) {
            amountInput.value = row.dataset.originalAmountValue;
            amountDisplay.textContent = row.dataset.originalAmountText;

            amountInput.classList.add("d-none");
            amountDisplay.classList.remove("d-none");
        }


        // --- RESTORE DATE ---
        const dateInput = row.querySelector('input[name="date"]');
        const dateDisplay = row.querySelector('.tx-date');
        
        if (dateInput && dateDisplay) {
            dateInput.value = row.dataset.originalDateValue;
            dateDisplay.textContent = row.dataset.originalDateText;

            // Sync flatpickr UI
            if (dateInput._flatpickr) {
                dateInput._flatpickr.setDate(row.dataset.originalDateValue, false);
            }
        
            dateInput.classList.add("d-none");
            dateDisplay.classList.remove("d-none");
        }
        
    
        // --- Restore NOTE ---
        const noteInput = row.querySelector('input[name="note"]');
        const noteDisplay = noteInput?.previousElementSibling;
        if (noteInput && noteDisplay) {
            noteInput.value = noteDisplay.textContent;
            noteInput.classList.add("d-none"); // hide input
            noteDisplay.classList.remove("d-none"); // show display
        }
    
        // --- Hide cancel/save buttons and show edit button ---
        buttons.forEach(b => b.classList.add("d-none"));
        if (editButton) editButton.classList.remove("d-none");
    
        // --- Hide all other inputs just in case ---
        inputs.forEach(i => i.classList.add("d-none"));
        displays.forEach(d => d.classList.remove("d-none"));
    
        // --- Exit edit mode ---
        row.dataset.editing = "false";
    }
    

    // ---- SAVE BUTTON CLICK ----
    if (saveBtn) {
        const row = saveBtn.closest(".transaction-row");
        if (!row) return;

        const txId = row.querySelector(".select-tx")?.value;
        const inputs = row.querySelectorAll(".tx-input");

        const changes = { transaction_id: txId };
        inputs.forEach(input => {
            if (!input.name) return;
            if (input.value !== input.dataset.originalValue) {
                changes[input.name] = input.value;
            }
        });

        if (Object.keys(changes).length === 1) return; // no changes
        updateTransactions(changes);
    }
});
        
    
        
    // -------------------------
    // UPDATE TRANSACTIONS
    // -------------------------
    function updateTransactions(changes) {
        const formData = new FormData();
    
        Object.entries(changes).forEach(([key, value]) => {
            formData.append(key, value);
        });
    
        formData.append(
            "csrfmiddlewaretoken",
            document.querySelector("input[name=csrfmiddlewaretoken]").value
        );
    
        fetch(UPDATE_TRANSACTIONS_URL, {
            method: "POST",
            credentials: "same-origin",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            console.log("Update response:", data);
        })
        .catch(err => console.error("Update failed:", err));
    }    


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
