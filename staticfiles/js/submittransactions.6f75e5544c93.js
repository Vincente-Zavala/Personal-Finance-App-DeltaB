document.addEventListener('DOMContentLoaded', function () {
    const submitBtn = document.getElementById('submittransactions');
    const pendingTable = document.getElementById('pendingTransactionsTable')

    if (!submitBtn || !pendingTable) return;

    function checkPendingSelections() {
        const rows = pendingTable.querySelectorAll("tr.transaction-row");
        let showButton = false;
    
        rows.forEach(row => {
            const categorySelect = row.querySelector(".category-select");
            if (!categorySelect || !categorySelect.value) return;
    
            const selectedOption = categorySelect.options[categorySelect.selectedIndex];
            const categoryType = (selectedOption.dataset.categorytype || "").toLowerCase();
    
            // If category requires destination, validate destination selection
            if (categoriesRequiringDestination.includes(categoryType)) {
                const destinationSelect = row.querySelector(".destination-cell select");
                if (!destinationSelect || !destinationSelect.value) {
                    return;
                }
            }
    
            // If we get here, at least ONE row is valid
            showButton = true;
        });
    
        submitBtn.style.display = showButton ? "inline-block" : "none";
    }
    


    // ONLY listen for category changes inside pending table
    pendingTable.addEventListener('change', function (e) {
        if (e.target.classList.contains('category-select')) {
            checkPendingSelections();
        }
    });

    function updateDeleteButtonVisibility() {
        const deleteBtn = document.getElementById("deletetransactions");
        if (!deleteBtn) return;
    
        // Look for any checked checkboxes in both tables
        const anyChecked = document.querySelectorAll(
            '#pendingTransactionsBody input[name="selectedtransactions"]:checked, ' +
            '#allTransactionsBody input[name="selectedtransactions"]:checked'
        ).length > 0;
    
        deleteBtn.style.display = anyChecked ? "inline-block" : "none";
    }

    window.updateDeleteButtonVisibility = updateDeleteButtonVisibility;
    
    
    document.addEventListener("change", function(e) {
        if (e.target.matches('input[name="selectedtransactions"]')) {
            updateDeleteButtonVisibility();
        }
    });

    updateDeleteButtonVisibility();
    
});

