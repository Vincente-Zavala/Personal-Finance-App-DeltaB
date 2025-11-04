document.querySelectorAll('input[name="selectedtransactions"]').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const transactionId = this.value;
        const goalId = this.closest('.goal-item').dataset.goalId;
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

        if (!response.ok) {
            alert("Something went wrong updating this transaction.");
            this.checked = !isChecked;
        }
    });
});
