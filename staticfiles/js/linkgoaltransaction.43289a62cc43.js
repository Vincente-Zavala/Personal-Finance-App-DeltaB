document.querySelectorAll('input[name="selectedtransactions"]').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const transactionId = this.value;
        const goalElement = this.closest('.goal-item');
        const goalId = goalElement.dataset.goalId;
        const isChecked = this.checked;

        const response = await fetch(linkGoalTransactionUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({
                goalid: goalId,
                transactionid: transactionId,
                checked: isChecked
            })
        });

        const data = await response.json();

        if (!response.ok || data.status !== "success") {
            alert("Something went wrong updating this transaction.");
            this.checked = !isChecked; // revert checkbox if failed
            return;
        }

        // If backend returns the updated saved amount, refresh it in the UI
        const savedAmountEl = goalElement.querySelector(".goal-saved-amount");
        if (savedAmountEl && data.saved !== undefined) {
            savedAmountEl.textContent = `$${parseFloat(data.saved).toFixed(2)}`;
