fetch("/previousmonthlimit/", {
    method: "GET",
    headers: {
        "X-Requested-With": "XMLHttpRequest"
    }
})
    .then(res => {
        if (!res.ok) {
            throw new Error("Server returned " + res.status);
        }
        return res.json();
    })
    .then(data => {
        console.log("Received:", data);
        if (data.status !== "ok") return;

        const previousLimits = data.previous_limits;

        table.querySelectorAll(".limit-input").forEach(input => {
            const match = input.name.match(/limit_(\d+)/);
            if (!match) return;

            const categoryId = match[1];

            input.value = previousLimits[categoryId] ?? "";
        });

        table.querySelectorAll(".limit-input").forEach(input => {
            const span = input.closest("td").querySelector(".limit-text");
            if (span) span.textContent = `$${input.value || "—"}`;
        });

    })
    .catch(err => console.error("Error fetching previous month:", err));
