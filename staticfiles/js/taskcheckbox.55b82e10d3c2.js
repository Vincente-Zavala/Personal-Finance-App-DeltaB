document.addEventListener('DOMContentLoaded', () => {
    // Loop through every checkbox
    document.querySelectorAll('.task-checkbox').forEach(box => {
        box.addEventListener('change', async (e) => {

            const item = e.target.closest('.task-item'); // the card div
            const taskId = item.dataset.taskId;          // from data-task-id attribute
            const completed = e.target.checked;          // true or false
            const text = item.querySelector('.task-text');

            // --- Update UI instantly ---
            if (completed) {
                text.classList.add('text-decoration-line-through', 'text-white-50');
                document.getElementById('completedtasks').appendChild(item);
                item.classList.add('opacity-75');
            } else {
                text.classList.remove('text-decoration-line-through', 'text-white-50');
                document.getElementById('activetasks').appendChild(item);
                item.classList.remove('opacity-75');
            }

            // --- Save to database (this is where fetch goes) ---
            try {
                await fetch(taskCompleteUrl, {  // 👈 this uses the variable defined in your template
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ id: taskId, complete: completed })
                });
            } catch (error) {
                console.error("Failed to update task:", error);
            }
        });
    });
});
