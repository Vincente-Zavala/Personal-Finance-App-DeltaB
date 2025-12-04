document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("transactionsForm");
    let clickedButtonAction = null;

    // Track any submit button click, even outside the form
    document.querySelectorAll("button[formaction]").forEach(btn => {
        btn.addEventListener("click", function() {
            clickedButtonAction = btn.getAttribute("formaction");
            // Trigger form submit manually
            form.requestSubmit(); 
        });
    });

    form.addEventListener("submit", function(e) {
        e.preventDefault();

        if (!clickedButtonAction) {
            console.error("No formaction detected!");
            return;
        }

        const formData = new FormData(form);

        fetch(clickedButtonAction, {
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
                data.deleted_ids?.forEach(id => {
                    const row = document.querySelector(`input[value='${id}']`)?.closest("tr");
                    if (row) row.remove();
                });

                // Hide pending table if empty
                const pendingBody = document.getElementById("pendingTransactionsBody");
                if (pendingBody && pendingBody.children.length === 0) {
                    const container = document.getElementById("pendingTransactionsContainer");
                    if (container) container.style.display = "none";
                }

                console.log("Action successful:", data);
            } else {
                alert("Error: " + data.error);
            }
        })
        .catch(err => console.error("AJAX error:", err));

        clickedButtonAction = null;
    });
});
