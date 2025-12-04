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
                        addTransactionsBody.appendChild(tr);
                    });
                }

                // --- Update account balances ---
                if (data.balances) {
                    updateAccountBalances(data.balances);
                }


                console.log("AJAX action successful:", data.deleted_ids);
            } else {
                alert("Error processing request.");
            }
        })
        .catch(err => console.error("AJAX error:", err));
    }
});
