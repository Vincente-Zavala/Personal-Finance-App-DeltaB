document.addEventListener("DOMContentLoaded", function() {
    const categoriesRequiringDestination = ["savings", "investment", "debt", "transfer", "retirement"];

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
                accountSelect.value = ""; // clear selection if hidden
            }
        });
    });
});
