const addTaskBtn = document.getElementById('addTaskBtn');
const newTaskInput = document.getElementById('newTaskInput');
const taskContainer = document.getElementById('taskContainer');

function createTask(text) {
    const task = document.createElement('div');
    task.className = 'task-card d-flex align-items-center justify-content-between p-3 rounded-3 bg-secondary shadow-sm';
    task.draggable = true;

    task.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <input type="checkbox" class="form-check-input m-0">
            <span class="task-text text-white">${text}</span>
        </div>
        <button class="btn btn-sm btn-outline-light rounded-circle p-1"><i class="fa fa-times"></i></button>
    `;

    // Delete task
    task.querySelector('button').addEventListener('click', () => task.remove());

    // Drag events
    task.addEventListener('dragstart', () => task.classList.add('dragging'));
    task.addEventListener('dragend', () => task.classList.remove('dragging'));

    return task;
}

// Add task
addTaskBtn.addEventListener('click', () => {
    const text = newTaskInput.value.trim();
    if (!text) return;
    const task = createTask(text);
    taskContainer.appendChild(task);
    newTaskInput.value = '';
});

// Drag & Drop
taskContainer.addEventListener('dragover', e => {
    e.preventDefault();
    const afterElement = getDragAfterElement(taskContainer, e.clientY);
    const dragging = document.querySelector('.dragging');
    if (!afterElement) {
        taskContainer.appendChild(dragging);
    } else {
        taskContainer.insertBefore(dragging, afterElement);
    }
});

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.task-card:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}
