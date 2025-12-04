document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("transactionsForm");
    const submitButton = document.getElementById("submittransactions");

    // Remove any existing click listeners to be safe
    submitButton.replaceWith(submitButton.cloneNode(true));
    const newSubmitButton = document.getElementById("submittransactions");

    newSubmitButton.addEventListener("click", function (e) {
        e.preventDefault(); // Prevent native form submit

        const formData = new FormData(form);
        const action = newSubmitButton.getAttribute("formaction");

        fetch(action, {
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
                // Remove submitted rows
                data.deleted_ids.forEach(id => {
                    const row = document.querySelector(`input[value='${id}']`)?.closest("tr");
                    if (row) row.remove();
                });

                // Hide pending table if empty
                const pendingBody = document.getElementById("pendingTransactionsBody");
                if (pendingBody && pendingBody.children.length === 0) {
                    const container = document.getElementById("pendingTransactionsContainer");
                    if (container) container.style.display = "none";
                }
                console.log("Pending transactions submitted:", data.deleted_ids);
            } else {
                alert("Error submitting transactions.");
            }
        })
        .catch(err => console.error("AJAX error:", err));
    }, { once: true }); // <-- ensures this listener only fires once
});
