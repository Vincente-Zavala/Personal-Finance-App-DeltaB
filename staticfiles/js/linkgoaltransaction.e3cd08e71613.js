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

            // ---- Update saved amount & progress bar for the current goal ----
            const currentGoalEl = document.querySelector(`.goal-item[data-goal-id='${data.goal_id}']`);
            if (currentGoalEl) {
                const savedAmountEl = currentGoalEl.querySelector(".goal-saved-amount");
                if (savedAmountEl) savedAmountEl.textContent = `$${parseFloat(data.saved).toFixed(2)}`;

                const goalAmount = parseFloat(currentGoalEl.dataset.goalAmount);
                const progressBar = currentGoalEl.querySelector(".progress-bar");
                if (progressBar && goalAmount > 0) {
                    const percent = Math.min((data.saved / goalAmount) * 100, 100);
                    progressBar.style.width = `${percent}%`;
                    progressBar.setAttribute("aria-valuenow", percent.toFixed(0));
                }
            }

            // ---- Update all checkboxes and × dynamically ----
            document.querySelectorAll('.goal-item').forEach(goalEl => {
                const gid = goalEl.dataset.goalId;

                goalEl.querySelectorAll('input[name="selectedtransactions"]').forEach(cb => {
                    const tid = cb.value;
                    const tr = cb.closest('tr');
                
                    // Remove existing ×
                    const existingX = tr.querySelector('.other-goal-x');
                    if (existingX) existingX.remove();
                
                    const isLinkedToOtherGoal = data.transaction_goal_map[gid] && data.transaction_goal_map[gid][tid];
                
                    if (isLinkedToOtherGoal && !cb.checked) {
                        // Transaction is linked to another goal → gray + X
                        cb.disabled = true;
                        const x = document.createElement('span');
                        x.textContent = '×';
                        x.classList.add('text-danger', 'fw-bold', 'ms-2', 'other-goal-x');
                        cb.insertAdjacentElement('afterend', x);
                    } else {
                        // Not linked → enable checkbox and remove any X
                        cb.disabled = false;
                    }
                });                
            });

        } catch (err) {
            console.error(err);
            alert("Error updating transaction");
            this.checked = !isChecked;
        }
    });
});