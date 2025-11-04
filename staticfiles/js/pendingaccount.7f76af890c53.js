document.addEventListener("DOMContentLoaded", function() {
    const categoriesRequiringDestination = ["savings", "investment", "debt", "transfer", "retirement"];
    const destinationHeader = document.getElementById("destinationHeader");

    function updateHeaderVisibility() {
        // Check if ANY destination account select is currently visible
        const hasVisibleAccount = Array.from(document.querySelectorAll(".account-select"))
            .some(select => select.offsetParent !== null); // visible if not display:none or detached

        // Toggle the header visibility
        destinationHeader.style.display = hasVisibleAccount ? "" : "none";

        // Toggle all destination cells for consistency
        document.querySelectorAll(".destination-cell").forEach(cell => {
            cell.style.display = hasVisibleAccount ? "" : "none";
        });
    }

    // Attach change listener to category dropdowns
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

    // Run once initially
    updateHeaderVisibility();
});
