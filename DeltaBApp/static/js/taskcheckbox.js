document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.task-checkbox').forEach(box => {
        box.addEventListener('change', async (e) => {
            const item = e.target.closest('.task-item');
            const taskId = item.dataset.taskId;
            const completed = e.target.checked;
            const text = item.querySelector('.task-text');

            // ✅ Update UI instantly
            if (completed) {
                text.classList.add('task-completed');
                document.getElementById('completedtasks').appendChild(item);
            } else {
                text.classList.remove('task-completed');
                document.getElementById('activetasks').appendChild(item);
            }

            // ✅ Update DB
            await fetch(taskCompleteUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ id: taskId, complete: completed })
            });
        });
    });
});
