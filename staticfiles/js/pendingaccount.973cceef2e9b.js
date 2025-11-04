document.addEventListener("DOMContentLoaded", function() {
    const categoriesRequiringDestination = ["savings", "investment", "debt", "transfer", "retirement"];
    const destinationHeader = document.getElementById("destinationHeader");

    function updateHeaderVisibility() {
        const hasVisibleAccount = Array.from(document.querySelectorAll(".account-select"))
            .some(select => select.offsetParent !== null);

        destinationHeader.style.display = hasVisibleAccount ? "" : "none";

        document.querySelectorAll(".destination-cell").forEach(cell => {
            cell.style.display = hasVisibleAccount ? "" : "none";
        });
    }

    document.querySelectorAll(".category-select").forEach(select => {
        select.addEventListener("change", function() {
            const selectedOption = this.options[this.selectedIndex];
            const rawType = selectedOption.getAttribute("data-categorytype") || "";
            const categoryType = rawType.trim().toLowerCase(); // normalize for comparison
            const transactionId = this.getAttribute("data-transaction-id");
            const accountSelect = document.getElementById(`accountchoice_${transactionId}`);

            console.log("Selected category type:", categoryType); // for debugging

            if (categoriesRequiringDestination.includes(categoryType)) {
                accountSelect.style.display = "inline-block";
            } else {
                accountSelect.style.display = "none";
                accountSelect.value = "";
            }

            updateHeaderVisibility();
        });
    });

    updateHeaderVisibility();
});
