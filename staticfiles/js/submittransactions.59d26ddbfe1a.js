document.addEventListener('DOMContentLoaded', function () {
    const submitBtn = document.getElementById('submittransactions');

    function checkSelections() {
        const selects = document.querySelectorAll('.category-select');
        let showButton = false;

        selects.forEach(select => {
            if (select.value !== "") {
                showButton = true;
            }
        });

        submitBtn.style.display = showButton ? "inline-block" : "none";
    }

    // 🔥 event delegation
    document.addEventListener('change', function (e) {
        if (e.target.classList.contains('category-select')) {
            checkSelections();
        }
    });
});
