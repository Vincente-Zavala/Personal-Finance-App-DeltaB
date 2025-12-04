// ---- Function to update progress for a goal ----
function updateGoalProgress(goalEl, savedAmount) {
    const savedAmountEl = goalEl.querySelector(".goal-saved-amount");
    if (savedAmountEl) {
        savedAmountEl.textContent = `$${parseFloat(savedAmount).toFixed(2)}`;
    }

    const goalAmount = parseFloat(goalEl.dataset.goalAmount);
    const progressBar = goalEl.querySelector(".progress-bar");
    if (progressBar && goalAmount > 0) {
        const percent = Math.min((savedAmount / goalAmount) * 100, 100);
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute("aria-valuenow", percent.toFixed(0));
    }
}

// ---- Initialize all progress bars on page load ----
document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        document.querySelectorAll(".goal-item").forEach(goalEl => {
            const savedAmountEl = goalEl.querySelector(".goal-saved-amount");
            if (!savedAmountEl) return;

            const rawSaved = savedAmountEl.textContent.replace(/[^0-9.-]/g, "");
            const savedAmount = parseFloat(rawSaved) || 0;

            // Clean commas from dataset
            const rawGoalAmount = goalEl.dataset.goalAmount.replace(/,/g, "");
            goalEl.dataset.goalAmount = rawGoalAmount;

            updateGoalProgress(goalEl, savedAmount);
        });
    }, 10); // Allow DOM to fully render
});


// ---- Checkbox listener for updating linked transactions ----
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
                updateGoalProgress(currentGoalEl, parseFloat(data.saved));
            }

            // ---- Update all checkboxes dynamically (disable/enable only, no ×) ----
            document.querySelectorAll('.goal-item').forEach(goalEl => {
                const gid = goalEl.dataset.goalId;

                goalEl.querySelectorAll('input[name="selectedtransactions"]').forEach(cb => {
                    const tid = cb.value;

                    const isLinkedToOtherGoal = data.transaction_goal_map[gid] && data.transaction_goal_map[gid][tid];

                    if (isLinkedToOtherGoal && !cb.checked) {
                        cb.disabled = true;
                    } else {
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
