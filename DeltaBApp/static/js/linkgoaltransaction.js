function updateGoalProgress(goalEl) {
    const savedAmount = parseFloat(goalEl.dataset.savedAmount) || 0;
    const goalAmount = parseFloat(goalEl.dataset.goalAmount.replace(/[^0-9.-]/g, "")) || 0;
    
    const savedAmountEl = goalEl.querySelector(".goal-saved-amount");
    if (savedAmountEl) {
        savedAmountEl.textContent = `$${savedAmount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    }

    const progressBar = goalEl.querySelector(".progress-bar");
    if (progressBar && goalAmount > 0) {
        const percent = Math.min((savedAmount / goalAmount) * 100, 100);
        
        progressBar.style.width = percent + "%";
        progressBar.setAttribute("aria-valuenow", percent.toFixed(0));
        
        const percentLabel = goalEl.querySelector(".goal-percent-text");
        if (percentLabel) percentLabel.textContent = `${percent.toFixed(0)}%`;
    }
}


document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        const goals = document.querySelectorAll(".goal-item");
        console.log(`SRE Check: Found ${goals.length} goals to process.`);

        goals.forEach(goalEl => {
            const saved = parseFloat(goalEl.dataset.savedAmount) || 0;
            const total = parseFloat(goalEl.dataset.goalAmount) || 0;
            
            console.log(`Goal ${goalEl.dataset.goalId}: Saved ${saved} / Total ${total}`);

            if (total > 0) {
                const percent = Math.min((saved / total) * 100, 100);
                
                const bar = goalEl.querySelector(".goal-progress-bar");
                
                if (bar) {
                    bar.style.width = percent + "%";
                    bar.setAttribute("aria-valuenow", percent.toFixed(0));
                    
                    const savedText = goalEl.querySelector(".goal-saved-amount");
                    if (savedText) {
                        savedText.textContent = `$${saved.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
                    }
                } else {
                    console.error("SRE Alert: Could not find .goal-progress-bar inside .goal-item");
                }
            }
        });
    }, 100);
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

            const currentGoalEl = document.querySelector(`.goal-item[data-goal-id='${data.goal_id}']`);
            if (currentGoalEl) {
                updateGoalProgress(currentGoalEl, parseFloat(data.saved));
            }

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
            this.checked = !isChecked;
        }
    });
});
