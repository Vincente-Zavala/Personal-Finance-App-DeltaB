document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("alltransactionsForm");
    const submitButton = document.getElementById("submittransactions");
    const deleteButton = document.getElementById("deletetransactions");
    const allTransactionsBody = document.getElementById("allTransactionsBody");

    const categoriesRequiringDestination = [
        "savings",
        "investment",
        "debt",
        "transfer",
        "retirement"
    ];

    function isPendingRowComplete(row) {
        const typeSelect = row.querySelector('.type-select');
        const categorySelect = row.querySelector('.category-select');
        const destinationSelect = row.querySelector('.account-select');
    
        if (!typeSelect || !typeSelect.value) return false;
        if (!categorySelect || !categorySelect.value) return false;
    
        const selectedOption = categorySelect.options[categorySelect.selectedIndex];
        const categoryType = (selectedOption?.dataset.categorytype || "").toLowerCase();
    
        if (categoriesRequiringDestination.includes(categoryType)) {
            if (!destinationSelect || !destinationSelect.value) return false;
        }
    
        return true;
    }


    function updatePendingSubmitVisibility() {
        const submitBtn = document.getElementById('submittransactions');
        const rows = document.querySelectorAll('#pendingTransactionsBody tr');
    
        const hasValid = Array.from(rows).some(row => isPendingRowComplete(row));
        submitBtn.style.display = hasValid ? "inline-block" : "none";
    }    
    

    // ---------------------------------
    // MARK ROWS FOR UPDATE (REPLACES .changed)
    // ---------------------------------
    document.addEventListener('change', function (e) {
        const row = e.target.closest('tr');
        if (!row) return;

        // Category change
        if (e.target.classList.contains('category-select')) {
            const select = e.target;
            const selectedOption = select.options[select.selectedIndex];
            const categoryType = selectedOption.dataset.categorytype || "";
        
            const hiddenInput = row.querySelector('.transaction-type-hidden');
            if (hiddenInput) {
                hiddenInput.value = categoryType;
                console.log("Set transaction type:", categoryType);
            }

            // ✅ mark row for UPDATE
            row.dataset.update = "true";
            console.log("Marked row for UPDATE:", row);
        }

        // Any editable input should also mark update
        if (e.target.classList.contains('tx-input')) {
            row.dataset.update = "true";
            console.log("Marked row for UPDATE:", row);
        }
    });

    // ---------------------------------
    // DELETE BUTTON
    // ---------------------------------
    deleteButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendFormAJAX(deleteButton.getAttribute("formaction"), false);
    });

    // ---------------------------------
    // SUBMIT BUTTON
    // ---------------------------------
    submitButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendFormAJAX(submitButton.getAttribute("formaction"), true);
    });

    // ---------------------------------
    // SUBMIT / DELETE LOGIC
    // ---------------------------------
    function sendFormAJAX(actionUrl, isSubmitPending) {
        const formData = new FormData();
    
        // Always include CSRF token
        formData.append(
            'csrfmiddlewaretoken',
            form.querySelector('[name=csrfmiddlewaretoken]').value
        );
    
        if (isSubmitPending) {
            const rows = form.querySelectorAll('#pendingTransactionsBody tr');
        
            let validRowCount = 0;
        
            rows.forEach(row => {
                if (!isPendingRowComplete(row)) return;
        
                validRowCount++;
        
                const inputs = row.querySelectorAll('select, input');
                inputs.forEach(input => {
                    if (input.name && input.value) {
                        formData.append(input.name, input.value);
                    }
                });
            });
        
            // Optional safety: prevent empty submits
            if (validRowCount === 0) {
                alert("Please complete at least one transaction before submitting.");
                return;
            }
        } else {
            // DELETE → send checked transactions
            const checked = form.querySelectorAll(
                "input[name='selectedtransactions']:checked"
            );
    
            checked.forEach(cb => {
                formData.append("selectedtransactions", cb.value);
            });
        }
    
        console.log("Sending form data:");
        for (let [key, value] of formData.entries()) {
            console.log(key, ":", value);
        }
    
        fetch(actionUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
                "X-Requested-With": "XMLHttpRequest"
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {

                if (data.deleted_ids) {
                    data.deleted_ids.forEach(id => {
                        const row = document
                            .querySelector(`input[value='${id}']`)
                            ?.closest("tr");
                        if (row) row.remove();
                    });
                }

                const pendingBody = document.getElementById("pendingTransactionsBody");
                if (pendingBody && pendingBody.children.length === 0) {
                    const container = document.getElementById("pendingTransactionsContainer");
                    if (container) container.style.display = "none";
                }

                if (isSubmitPending && data.new_transactions) {
                    data.new_transactions.forEach(tx => {
                        const tr = document.createElement("tr");
                        tr.classList.add("transaction-row");
                        tr.setAttribute("data-type", tx.type.toLowerCase());
                        tr.innerHTML = `
                            <td class="editcol" hidden>
                                <input class="form-check-input" type="checkbox"
                                       name="selectedtransactions" value="${tx.id}">
                            </td>
                            <td>${tx.date}</td>
                            <td class="category-cell">${tx.type}</td>
                            <td>${tx.category}</td>
                            <td class="text-truncate" style="max-width:150px;"
                                title="${tx.note}">${tx.note}</td>
                            <td>${tx.account}</td>
                            <td class="text-end fw-semibold text-primary amount-cell">
                                $${tx.amount}
                            </td>
                        `;
                        allTransactionsBody.appendChild(tr);
                    });
                }

                updatePendingSubmitVisibility();
                fetchAccountBalances();
            } else {
                alert("Error processing request.");
            }
        })
        .catch(err => console.error("AJAX error:", err));
    }
});
