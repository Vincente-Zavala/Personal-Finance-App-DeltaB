document.addEventListener("DOMContentLoaded", function() {
    // Select all category limit forms
    const budgetForms = document.querySelectorAll("form[action^='/edit_categorytype_limits/']");

    budgetForms.forEach(form => {
        form.addEventListener("submit", function(e) {
            e.preventDefault(); // prevent full page reload

            const formData = new FormData(form);
            const actionUrl = form.getAttribute("action");

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
                    // Update the table with new budget values
                    for (const [categoryId, limit] of Object.entries(data.updated_limits)) {
                        const row = form.querySelector(`input[name='limit_${categoryId}']`);
                        if (row) {
                            row.value = limit;
                            const span = row.closest("td").querySelector(".limit-text");
                            if (span) span.textContent = `$${limit}`;
                        }
                    }

                    // Optionally show a small success message
                    console.log("Budget limits updated successfully!");
                } else {
                    console.error("Error updating budget:", data.message);
                }
            })
            .catch(err => console.error("AJAX error:", err));
        });
    });
});
