document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.task-checkbox').forEach(box => {
        box.addEventListener('change', async (e) => {
            const item = e.target.closest('.task-item');
            const taskId = item.dataset.taskId;
            const completed = e.target.checked;
            const text = item.querySelector('.task-text');
            
            // Update UI
            if (completed) {
                text.classList.add('task-completed'); // 👈 add your red style class
                document.getElementById('completedtasks').appendChild(item);
                item.classList.add('opacity-75');
            } else {
                text.classList.remove('task-completed'); // 👈 remove it when unchecked
                document.getElementById('activetasks').appendChild(item);
                item.classList.remove('opacity-75');
            }

            // Update in DB
            await fetch(taskCompleteUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ id: taskId, complete: completed })
            });
        });
    });
});
