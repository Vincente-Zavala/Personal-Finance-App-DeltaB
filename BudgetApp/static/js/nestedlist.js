var toggler = document.getElementsByClassName("caret");
var i;

document.addEventListener("DOMContentLoaded", function() {
    for (i = 0; i < toggler.length; i++) {
    toggler[i].addEventListener("click", function() {
        this.parentElement.querySelector(".nested").classList.toggle("active");
        this.classList.toggle("caret-down");
    });
    }
});


document.querySelectorAll(".parent-checkbox").forEach(function(parent) {
    parent.addEventListener("change", function() {
        // Find all child checkboxes inside the same <li>
        const nestedCheckboxes = parent.closest("li").querySelectorAll(".child-checkbox");
        nestedCheckboxes.forEach(cb => cb.checked = parent.checked);
    });
});