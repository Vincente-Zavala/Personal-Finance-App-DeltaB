document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("transactionsForm");
    const submitButton = document.getElementById("submittransactions");
    const deleteButton = document.getElementById("deletetransactions");

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
                data.deleted_ids?.forEach(id => {
                    const row = document.querySelector(`input[value='${id}']`)?.closest("tr");
                    if (row) row.remove();
                });

                const pendingBody = document.getElementById("pendingTransactionsBody");
                if (pendingBody && pendingBody.children.length === 0) {
                    const container = document.getElementById("pendingTransactionsContainer");
                    if (container) container.style.display = "none";
                }
                console.log("AJAX action successful:", data.deleted_ids);
            } else {
                alert("Error: " + (data.error || "Unknown"));
            }
        })
        .catch(err => console.error("AJAX error:", err));
    }

    // Only click listeners, no form submit
    submitButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendFormAJAX(submitButton.getAttribute("formaction"));
    });

    deleteButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendFormAJAX(deleteButton.getAttribute("formaction"));
    });
});
