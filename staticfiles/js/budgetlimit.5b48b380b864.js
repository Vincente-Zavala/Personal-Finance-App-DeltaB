document.addEventListener("DOMContentLoaded", function() {
    const saveButtons = document.querySelectorAll(".save-btn");

    saveButtons.forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.preventDefault(); // prevent normal form submit
            const form = btn.closest("form"); // get the parent form
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
                    // update table values
                    for (const [categoryId, limit] of Object.entries(data.updated_limits)) {
                        const row = form.querySelector(`input[name='limit_${categoryId}']`);
                        if (row) {
                            row.value = limit;
                            const span = row.closest("td").querySelector(".limit-text");
                            if (span) span.textContent = `$${limit}`;
                        }
                    }
                    console.log("Budget limits updated successfully!");
                } else {
                    console.error("Error updating budget:", data.message);
                }
            })
            .catch(err => console.error("AJAX error:", err));
        });
    });
});
