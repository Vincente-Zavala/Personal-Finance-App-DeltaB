document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("transactionsForm");
    const deleteButton = document.getElementById("deletetransactions");

    if (!form || !deleteButton) return; // Page does not have delete support

    // Delete Selected Transactions
    deleteButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendFormAJAX(deleteButton.getAttribute("formaction"));
    });

    function sendFormAJAX(actionUrl) {
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

                // Remove deleted rows
                if (data.deleted_ids) {
                    data.deleted_ids.forEach(id => {
                        const row = document.querySelector(`input[value='${id}']`)?.closest("tr");
                        if (row) row.remove();
                    });
                }

                // Hide Pending section if empty
                const pendingBody = document.getElementById("pendingTransactionsBody");
                if (pendingBody && pendingBody.children.length === 0) {
                    const container = document.getElementById("pendingTransactionsContainer");
                    if (container) container.style.display = "none";
                }

                console.log("Delete successful:", data.deleted_ids);
            } else {
                alert("Error deleting transactions.");
            }
        })
        .catch(err => console.error("AJAX delete error:", err));
    }
});
