document.addEventListener("DOMContentLoaded", function () {
    console.log("datedropdown.js loaded ✅");  // test log
});

document.addEventListener("DOMContentLoaded", function () {
    // When year is checked -> check all months/days under it
    document.querySelectorAll(".year-check").forEach(yearBox => {
        yearBox.addEventListener("change", function () {
            const year = this.dataset.year;
            document.querySelectorAll("[data-year='" + year + "']").forEach(box => {
                box.checked = this.checked;
            });
        });
    });

    // When month is checked -> check all days under it
    document.querySelectorAll(".month-check").forEach(monthBox => {
        monthBox.addEventListener("change", function () {
            const year = this.dataset.year;
            const month = this.dataset.month;
            document.querySelectorAll("[data-year='" + year + "'][data-month='" + month + "']").forEach(box => {
                box.checked = this.checked;
            });
        });
    });
});