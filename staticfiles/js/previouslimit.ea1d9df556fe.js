document.addEventListener("DOMContentLoaded", function () {

    // Handle clicking "Previous Month Budgets"
    document.querySelectorAll(".previous-btn").forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();

            const tableId = btn.dataset.target;
            const table = document.getElementById(tableId);

            fetch("/previousmonthlimit/")
                .then(res => res.json())
                .then(data => {
                    if (data.status !== "ok") return;

                    const previousLimits = data.previous_limits;

                    // Populate each input inside THIS table only
                    table.querySelectorAll(".limit-input").forEach(input => {
                        const match = input.name.match(/limit_(\d+)/);
                        if (!match) return;

                        const categoryId = match[1];

                        if (previousLimits[categoryId] !== undefined) {
                            input.value = previousLimits[categoryId];
                        } else {
                            input.value = "";
                        }
                    });

                    // Optional: update span text live (if desired)
                    table.querySelectorAll(".limit-input").forEach(input => {
                        const span = input.closest("td").querySelector(".limit-text");
                        if (span) span.textContent = `$${input.value || "—"}`;
                    });

                })
                .catch(err => console.error("Error fetching previous month:", err));
        });
    });

});
