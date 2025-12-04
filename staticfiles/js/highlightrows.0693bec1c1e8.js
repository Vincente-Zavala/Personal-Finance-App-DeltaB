document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll(".transaction-row");

    rows.forEach(row => {
        row.addEventListener("click", function () {
            // Remove highlight from other rows
            rows.forEach(r => r.classList.remove("selected-row"));
            rows.forEach(r => r.classList.remove("amount-cell"));
            // Add highlight to clicked row
            this.classList.add("selected-row");
        });
    });
});