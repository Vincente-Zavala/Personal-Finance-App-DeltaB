// ---- Function to update progress for a goal ----
function updateGoalProgress(goalEl) {
    // 1. Pull data directly from dataset (The SRE "Source of Truth")
    const savedAmount = parseFloat(goalEl.dataset.savedAmount) || 0;
    const goalAmount = parseFloat(goalEl.dataset.goalAmount.replace(/[^0-9.-]/g, "")) || 0;
    
    // 2. Update the Text Label
    const savedAmountEl = goalEl.querySelector(".goal-saved-amount");
    if (savedAmountEl) {
        savedAmountEl.textContent = `$${savedAmount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    }

    // 3. Update the Bar
    const progressBar = goalEl.querySelector(".progress-bar");
    if (progressBar && goalAmount > 0) {
        const percent = Math.min((savedAmount / goalAmount) * 100, 100);
        
        // Ensure the style property is applied correctly
        progressBar.style.width = percent + "%";
        progressBar.setAttribute("aria-valuenow", percent.toFixed(0));
        
        // Optional: Update a percentage label if you have one
        const percentLabel = goalEl.querySelector(".goal-percent-text");
        if (percentLabel) percentLabel.textContent = `${percent.toFixed(0)}%`;
    }
}

// ---- Initialize all progress bars ----
document.addEventListener("DOMContentLoaded", () => {
    // Small delay to ensure the DOM is fully painted
    setTimeout(() => {
        const goals = document.querySelectorAll(".goal-item");
        console.log(`SRE Check: Found ${goals.length} goals to process.`);

        goals.forEach(goalEl => {
            // 1. Get raw numbers from dataset
            const saved = parseFloat(goalEl.dataset.savedAmount) || 0;
            const total = parseFloat(goalEl.dataset.goalAmount) || 0;
            
            console.log(`Goal ${goalEl.dataset.goalId}: Saved ${saved} / Total ${total}`);

            if (total > 0) {
                const percent = Math.min((saved / total) * 100, 100);
                
                // 2. Target the bar using the specific class from your HTML
                const bar = goalEl.querySelector(".goal-progress-bar");
                
                if (bar) {
                    // Force the width update
                    bar.style.width = percent + "%";
                    bar.setAttribute("aria-valuenow", percent.toFixed(0));
                    
                    // Update the text label just in case it's blank
                    const savedText = goalEl.querySelector(".goal-saved-amount");
                    if (savedText) {
                        savedText.textContent = `$${saved.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
                    }
                } else {
                    console.error("SRE Alert: Could not find .goal-progress-bar inside .goal-item");
                }
            }
        });
    }, 100); // 100ms delay for stability
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
            // alert("Error updating transaction");
            this.checked = !isChecked;
        }
    });
});
