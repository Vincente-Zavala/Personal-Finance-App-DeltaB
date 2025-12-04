document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("transactionsForm");
    const submitButton = document.getElementById("submittransactions");
    const deleteButton = document.getElementById("deletetransactions");
    const allTransactionsBody = document.querySelector("#transactionsForm ~ div table tbody"); // Adjust selector to your All Transactions table

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

    function sendFormAJAX(actionUrl, isSubmitPending) {
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

                // Hide Pending Transactions if empty
                const pendingBody = document.getElementById("pendingTransactionsBody");
                if (pendingBody && pendingBody.children.length === 0) {
                    const container = document.getElementById("pendingTransactionsContainer");
                    if (container) container.style.display = "none";
                }

                // If these were pending transactions submitted, append them to All Transactions
                if (isSubmitPending && data.new_transactions_html) {
                    allTransactionsBody.insertAdjacentHTML("beforeend", data.new_transactions_html);
                }

                console.log("AJAX action successful:", data.deleted_ids);
            } else {
                alert("Error processing request.");
            }
        })
        .catch(err => console.error("AJAX error:", err));
    }
});