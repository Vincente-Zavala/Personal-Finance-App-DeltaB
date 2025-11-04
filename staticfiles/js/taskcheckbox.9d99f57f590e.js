document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.task-checkbox').forEach(box => {
        box.addEventListener('change', async (e) => {
            const item = e.target.closest('.task-item');
            const taskId = item.dataset.taskId;
            const completed = e.target.checked;
            const text = item.querySelector('.task-text');
            
            // Update UI
            if (completed) {
                text.classList.add('text-decoration-line-through', 'text-white-50');
                document.getElementById('completedtasks').appendChild(item);
                item.classList.add('opacity-75');
            } else {
                text.classList.remove('text-decoration-line-through', 'text-white-50');
                document.getElementById('activetasks').appendChild(item);
                item.classList.remove('opacity-75');
            }

            // Optional: Update in DB using fetch
            fetch("{% url 'taskcomplete' %}", {
                method: "POST",
                headers: {
                    "X-CSRFToken": "{{ csrf_token }}",
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ id: taskId, complete: completed })
            });
        });
    });
});