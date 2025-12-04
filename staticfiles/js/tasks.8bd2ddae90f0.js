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

    return task;
}
