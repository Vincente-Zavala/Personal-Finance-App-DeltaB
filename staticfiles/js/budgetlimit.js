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
                        const input = form.querySelector(`input[name='limit_${categoryId}']`);
                        const span = input.closest("td").querySelector(".limit-text");
                        if (input && span) {
                            input.value = limit;
                            span.textContent = `$${limit}`;
                        }
                    }

                    // update category type totals
                    for (const [typeId, total] of Object.entries(data.updated_type_totals)) {
                        const card = document.querySelector(`.category-card[data-type-id='${typeId}'] h6`);
                        if (card) card.textContent = `$${total}`;
                    }

                    // --- TOGGLE BUTTONS AND INPUTS BACK ---
                    const tableId = btn.dataset.target;
                    const table = document.getElementById(tableId);

                    // hide input, show spans
                    table.querySelectorAll(".limit-input").forEach(input => input.classList.add("d-none"));
                    table.querySelectorAll(".limit-text").forEach(span => span.classList.remove("d-none"));

                    // toggle buttons
                    btn.classList.add("d-none"); // hide Save
                    form.querySelector(".cancel-btn").classList.add("d-none"); // hide Cancel
                    form.querySelector(".edit-btn").classList.remove("d-none"); // show Edit

                    console.log("Budget limits updated successfully!");
                } else {
                    console.error("Error updating budget:", data.message);
                }
            })
            .catch(err => console.error("AJAX error:", err));
        });
    });
});
