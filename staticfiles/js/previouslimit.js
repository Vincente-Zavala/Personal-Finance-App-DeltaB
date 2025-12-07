document.addEventListener("DOMContentLoaded", function () {
    // Handle clicking "Previous Month Budgets"
    document.querySelectorAll(".previous-btn").forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault(); // prevent form submission

            // Find the table this button belongs to
            const tableId = btn.dataset.target;
            const table = document.getElementById(tableId);
            if (!table) return;

            // Fetch previous month limits from Django
            fetch("/previousmonthlimit/", {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(res => {
                if (!res.ok) throw new Error("Server returned " + res.status);
                return res.json();
            })
            .then(data => {
                if (data.status !== "ok") return;

                const previousLimits = data.previous_limits;

                // Populate inputs inside this table only
                table.querySelectorAll(".limit-input").forEach(input => {
                    const match = input.name.match(/limit_(\d+)/);
                    if (!match) return;

                    const categoryId = match[1];

                    input.value = previousLimits[categoryId] ?? "";
                });

                // Update span text live
                table.querySelectorAll(".limit-input").forEach(input => {
                    const span = input.closest("td").querySelector(".limit-text");
                    if (span) span.textContent = `$${input.value || "—"}`;
                });

                console.log("Previous month budgets populated successfully!");
            })
            .catch(err => console.error("Error fetching previous month:", err));
        });
    });
});
