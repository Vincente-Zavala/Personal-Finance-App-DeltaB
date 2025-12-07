document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".edit-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const tableId = this.getAttribute("data-target");
            const table = document.getElementById(tableId);
            table.querySelectorAll(".limit-text").forEach(el => el.classList.add("d-none"));
            table.querySelectorAll(".limit-input").forEach(el => el.classList.remove("d-none"));

            // show save/cancel buttons
            this.closest(".bg-secondary").querySelector(".save-btn").classList.remove("d-none");
            this.closest(".bg-secondary").querySelector(".cancel-btn").classList.remove("d-none");
            this.closest(".bg-secondary").querySelector(".previous-btn").classList.remove("d-none");
            this.classList.add("d-none");
        });
    });

    document.querySelectorAll(".cancel-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const tableId = this.getAttribute("data-target");
            const table = document.getElementById(tableId);
            table.querySelectorAll(".limit-text").forEach(el => el.classList.remove("d-none"));
            table.querySelectorAll(".limit-input").forEach(el => el.classList.add("d-none"));

            // hide save/cancel, show edit
            this.closest(".bg-secondary").querySelector(".save-btn").classList.add("d-none");
            this.closest(".bg-secondary").querySelector(".previous-btn").classList.add("d-none");
            this.closest(".bg-secondary").querySelector(".edit-btn").classList.remove("d-none");
            this.classList.add("d-none");
        });
    });
});
