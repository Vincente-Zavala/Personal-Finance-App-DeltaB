document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("addtransactionsForm");
    const submitButton = document.getElementById("addtransactions");
    const deleteButton = document.getElementById("deletetransactions");
    
    const addTransactionsBody = document.getElementById("addTransactionsBody");

    // Submit Pending Transactions
    submitButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendFormAJAX(submitButton.getAttribute("formaction"), true);
    });

    // Delete Selected Transactions
    deleteButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendFormAJAX(deleteButton.getAttribute("formaction"), false);
    });

    let duplicatesSubmitUrl = "/addtransaction/"; // default for adding transactions


    function sendFormAJAX(actionUrl, isSubmitNew) {
        const formData = new FormData(form);
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

                if (actionUrl.includes("duplicateaddtransaction")) {
                    console.log("No duplicates found — auto-submitting to addtransaction...");
                    return sendFormAJAX("/addtransaction/", true);
                }

                // Remove submitted/deleted rows from Pending Transactions
                if (data.deleted_ids) {
                    data.deleted_ids.forEach(id => {
                        const row = document.querySelector(`input[value='${id}']`)?.closest("tr");
                        if (row) row.remove();
                    });
                }

                // If these were pending transactions submitted, append them to All Transactions
                if (isSubmitNew && data.add_transactions) {
                    data.add_transactions.forEach(tx => {
                        const tr = document.createElement("tr");
                        tr.classList.add("transaction-row");
                        tr.setAttribute("data-type", tx.category_type.toLowerCase());
                        tr.innerHTML = `
                            <td class="editcol" hidden>
                                <input class="form-check-input" type="checkbox" name="selectedtransactions" value="${tx.id}">
                            </td>
                            <td>${tx.date}</td>
                            <td class="category-cell">${tx.category_type}</td>
                            <td>${tx.category}</td>
                            <td class="text-truncate" style="max-width:150px;" title="${tx.note}">${tx.note}</td>
                            <td>${tx.account}</td>
                            <td class="text-end fw-semibold text-primary amount-cell">$${tx.amount}</td>
                        `;
                        addTransactionsBody.prepend(tr);
                    });

                    // --- Clear form inputs except transaction type ---
                    const fieldsToKeep = ["inputtransaction"];
                    Array.from(form.elements).forEach(el => {
                        if (!fieldsToKeep.includes(el.name)) {
                            if (el.tagName === "INPUT") {
                                if (el.type === "text" || el.type === "number" || el.type === "date") {
                                    el.value = "";
                                } else if (el.type === "checkbox" || el.type === "radio") {
                                    el.checked = false;
                                }
                            } else if (el.tagName === "SELECT") {
                                el.selectedIndex = 0; // reset to first option
                            } else if (el.tagName === "TEXTAREA") {
                                el.value = "";
                            }
                        }
                    });

                }

                // --- Update account balances ---
                fetchAccountBalances();

                console.log("AJAX action successful:", data.deleted_ids);


            } else if (data.status === "duplicates") {
                // -------------------------------
                // Handle duplicates modal
                // -------------------------------
                const tbody = document.getElementById("manualduplicatesTableBody");
                console.log("No duplicates found — auto-submitting to addtransaction...");

                let totalDuplicates = 0;

                data.groups.forEach(group => {
                    totalDuplicates++;

                    // NEW ROW
                    const newTx = group.new;
                    tbody.insertAdjacentHTML("beforeend", `
                        <tr class="table-warning transaction-row">
                            <td>${newTx.date}</td>
                            <td class="text-truncate" style="max-width: 200px;">${newTx.note}</td>
                            <td>${newTx.account}</td>
                            <td class="text-end amount-cell">$${newTx.amount}</td>
                            <td>New Row</td>
                        </tr>
                    `);

                    // EXISTING MATCHES
                    group.existing.forEach(ex => {
                        tbody.insertAdjacentHTML("beforeend", `
                            <tr class="table-danger">
                                <td>${ex.date}</td>
                                <td>${ex.note}</td>
                                <td>${ex.account}</td>
                                <td class="text-end">$${ex.amount}</td>
                                <td>Existing</td>
                            </tr>
                        `);
                    });

                    // Add small space between groups
                    tbody.insertAdjacentHTML("beforeend", `
                        <tr><td colspan="5" class="bg-dark border-0" style="height: 8px;"></td></tr>
                    `);
                });

                // Update duplicate counter
                document.getElementById("duplicateCount").textContent = totalDuplicates;

                // Show duplicates modal
                const modalEl = document.getElementById("manualduplicatesModal");
                const modal = new bootstrap.Modal(modalEl);
                modal.show();

                // Attach Continue button to submit the add transaction form
                confirmImportBtn.onclick = function(e) {
                    e.preventDefault();
                    const modalEl = document.getElementById("manualduplicatesModal");
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                
                    sendFormAJAX(duplicatesSubmitUrl, true);
                };
                



            } else {
                alert("Error processing request.");
            }
        })
        .catch(err => console.error("AJAX error:", err));
    }
});
