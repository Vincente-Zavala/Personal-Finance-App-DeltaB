document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll(".transaction-row");

    rows.forEach(row => {
        row.addEventListener("click", function () {
            // Remove highlight from all rows
            rows.forEach(r => {
                r.querySelectorAll("td").forEach(td => td.classList.remove("selected-cell"));
            });

            // Highlight only the td's except editcol
            row.querySelectorAll("td:not(.editcol)").forEach(td => td.classList.add("selected-cell"));
        });
    });
});
