document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll(".transaction-row");

    rows.forEach(row => {
        row.addEventListener("click", function () {
            // Remove highlight from other rows
            rows.forEach(r => r.classList.remove("selected-row"));
            // Add highlight to clicked row
            this.classList.add("selected-row");
        });
    });
});