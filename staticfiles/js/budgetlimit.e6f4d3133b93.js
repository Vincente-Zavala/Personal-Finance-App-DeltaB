document.addEventListener("input", function (e) {
    if (e.target.classList.contains("limit-input")) {

        const budgetId = e.target.dataset.budgetId;
        const newLimit = e.target.value;

        fetch(window.budgetSettings.updateUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": window.budgetSettings.csrfToken,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `budget_id=${budgetId}&limit=${newLimit}`
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                console.log("Budget limit updated");
            } else {
                console.error("Error:", data.error);
            }
        });
    }
});
