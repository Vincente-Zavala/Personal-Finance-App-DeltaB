document.addEventListener("DOMContentLoaded", function () {
    // Select all rows with the class "transaction-row"
    const rows = document.querySelectorAll(".transaction-row");

    rows.forEach(row => {
        row.addEventListener("click", function (e) {
            // Skip if the click is on the checkbox
            if (e.target.tagName.toLowerCase() === "input") return;

            // Remove highlight from all rows
            rows.forEach(r => r.classList.remove("selected-row"));

            // Add highlight to clicked row
            this.classList.add("selected-row");
        });
    });
});
