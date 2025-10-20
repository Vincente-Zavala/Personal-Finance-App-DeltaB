document.addEventListener('DOMContentLoaded', function() {
    const categorySelects = document.querySelectorAll('.category-select');
    const submitBtn = document.getElementById('submittransactions');

    function checkSelections() {
        let showButton = false;
        categorySelects.forEach(select => {
            if (select.value !== "") {
                showButton = true;
            }
        });
        submitBtn.style.display = showButton ? "inline-block" : "none";
    }

    categorySelects.forEach(select => {
        select.addEventListener('change', checkSelections);
    });
});