document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll(".transaction-row");

    rows.forEach(row => {
        row.addEventListener("click", function () {

            // Add highlight to clicked row
            this.classList.add("selected-row");
        });
    });
});