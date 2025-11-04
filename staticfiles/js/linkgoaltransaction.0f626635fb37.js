document.querySelectorAll('input[name="selectedtransactions"]').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const transactionId = this.value;
        const goalId = "{{ goal.id }}";  // assuming you're in a goal detail view
        const isChecked = this.checked;

        // Send update to backend
        const response = await fetch("{% url 'linkgoaltransaction' %}", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}",
            },
            body: JSON.stringify({
                goalid: goalId,
                transactionid: transactionId,
                checked: isChecked
            })
        });

        if (!response.ok) {
            alert("Something went wrong updating this transaction.");
            this.checked = !isChecked; // revert if failed
        }
    });
});
