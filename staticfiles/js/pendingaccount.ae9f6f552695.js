document.addEventListener("DOMContentLoaded", function() {
    const categoriesRequiringDestination = ["savings", "investment", "debt", "transfer", "retirement"];
    const destinationHeader = document.getElementById("destinationHeader");

    function updateHeaderVisibility() {
        const visibleAccounts = document.querySelectorAll(".account-select:not([style*='display: none'])");
        destinationHeader.style.display = visibleAccounts.length > 0 ? "" : "none";
        
        // Hide or show all cells for consistency
        document.querySelectorAll(".destination-cell").forEach(cell => {
            cell.style.display = visibleAccounts.length > 0 ? "" : "none";
        });
    }

    document.querySelectorAll(".category-select").forEach(select => {
        select.addEventListener("change", function() {
            const selectedOption = this.options[this.selectedIndex];
            const categoryType = selectedOption.getAttribute("data-categorytype");
            const transactionId = this.getAttribute("data-transaction-id");
            const accountSelect = document.getElementById(`accountchoice_${transactionId}`);

            if (categoriesRequiringDestination.includes(categoryType)) {
                accountSelect.style.display = "inline-block";
            } else {
                accountSelect.style.display = "none";
                accountSelect.value = "";
            }

            updateHeaderVisibility();
        });
    });

    // Hide header initially
    updateHeaderVisibility();
});