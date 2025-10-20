document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("toggleEdit").addEventListener("click", function() {
        let editCols = document.querySelectorAll(".editcol");
        editCols.forEach(col => {
            if (col.hasAttribute("hidden")) {
                col.removeAttribute("hidden");
            } else {
                col.setAttribute("hidden", true);
            }
        });
    });
});
