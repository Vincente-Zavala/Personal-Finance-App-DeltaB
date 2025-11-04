document.querySelectorAll('input[name="selectedtransactions"]').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const transactionId = this.value;
        const goalElement = this.closest('.goal-item');
        const goalId = goalElement.dataset.goalId;
        const isChecked = this.checked;

        try {
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
                this.checked = !isChecked;
                return;
            }

            // Update saved amount
            const savedAmountEl = goalElement.querySelector(".goal-saved-amount");
            if (savedAmountEl && data.saved !== undefined) {
                savedAmountEl.textContent = `$${parseFloat(data.saved).toFixed(2)}`;
            }

            // Update progress bar
            const goalAmount = parseFloat(goalElement.dataset.goalAmount);
            const progressBar = goalElement.querySelector(".progress-bar");
            if (progressBar && data.saved !== undefined && goalAmount > 0) {
                const percent = Math.min((data.saved / goalAmount) * 100, 100);
                progressBar.style.width = `${percent}%`;
                progressBar.setAttribute("aria-valuenow", percent.toFixed(0));
            }

            // ✅ Update disabled checkboxes and "×" dynamically
            document.querySelectorAll('input[name="selectedtransactions"]').forEach(cb => {
                const tr = cb.closest('tr');
                const tid = cb.value;
                const other = data.other_goals_map[tid];

                // Remove existing × first
                const existingX = tr.querySelector('.other-goal-x');
                if (existingX) existingX.remove();

                if (other && !cb.checked) {
                    cb.disabled = true;
                    const x = document.createElement('span');
                    x.textContent = '×';
                    x.classList.add('text-danger', 'fw-bold', 'ms-2', 'other-goal-x');
                    cb.insertAdjacentElement('afterend', x);
                } else {
                    cb.disabled = false;
                }
            });

        } catch (err) {
            console.error(err);
            alert("Error updating transaction");
            this.checked = !isChecked;
        }
    });
});