document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("deletetransactionForm");

    form.addEventListener("submit", function (e) {
        e.preventDefault(); // Stop full page reload

        const formData = new FormData(form);

        fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": formData.get("csrfmiddlewaretoken")
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {

                // Remove deleted rows from DOM
                data.deleted_ids.forEach(id => {
                    const row = document.querySelector(`input[value='${id}']`)
                                    ?.closest("tr");

                    if (row) row.remove();
                });

                // Optional: success message
                console.log("Deleted:", data.deleted_ids);
            } else {
                alert("Error: " + data.error);
            }
        })
        .catch(err => console.error("AJAX error:", err));
    });
});
