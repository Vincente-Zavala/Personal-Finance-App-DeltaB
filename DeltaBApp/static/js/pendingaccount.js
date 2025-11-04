document.addEventListener("DOMContentLoaded", function() {
    const categoriesRequiringDestination = ["savings", "investment", "debt", "transfer", "retirement"];
    const destinationHeader = document.getElementById("destinationHeader");

    function updateHeaderVisibility() {
        const hasVisibleAccount = Array.from(document.querySelectorAll(".destination-cell"))
            .some(cell => cell.style.display !== "none");
        destinationHeader.style.display = hasVisibleAccount ? "" : "none";
    }

    document.querySelectorAll(".category-select").forEach(select => {
        select.addEventListener("change", function() {
            const selectedOption = this.options[this.selectedIndex];
            const categoryType = (selectedOption.getAttribute("data-categorytype") || "").trim().toLowerCase();
            const transactionId = this.getAttribute("data-transaction-id");
            const accountSelect = document.getElementById(`accountchoice_${transactionId}`);
            const destinationCell = accountSelect.closest(".destination-cell");

            console.log("Selected category:", selectedOption.text, "| Type:", categoryType);

            if (categoriesRequiringDestination.includes(categoryType)) {
                accountSelect.style.display = "inline-block";
                destinationCell.style.display = "";
                console.log("→ Showing destination account");
            } else {
                accountSelect.style.display = "none";
                destinationCell.style.display = "none";
                accountSelect.value = "";
                console.log("→ Hiding destination account");
            }

            updateHeaderVisibility();
        });
    });

    // Initialize header state
    updateHeaderVisibility();
});
