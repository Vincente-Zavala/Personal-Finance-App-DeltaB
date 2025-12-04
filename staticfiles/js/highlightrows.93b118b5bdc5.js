document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll(".transaction-row");

    rows.forEach(row => {
        row.addEventListener("click", function (e) {
            // Skip if the click is directly on the editcol cell or the checkbox
            if (
                e.target.tagName.toLowerCase() === "input" ||
                e.target.classList.contains("editcol")
            ) return;

            // Remove highlight from all rows
            rows.forEach(r => r.classList.remove("selected-row"));

            // Add highlight to clicked row
            this.classList.add("selected-row");
        });
    });
});
