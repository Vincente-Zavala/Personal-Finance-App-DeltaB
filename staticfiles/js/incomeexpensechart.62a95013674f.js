document.addEventListener("DOMContentLoaded", () => {
    const dataEl = document.getElementById("incomeexpense-chart-data");
    if (!dataEl) return console.error("No incomeexpense-chart-data element found.");

    let chartsData;
    try {
        chartsData = JSON.parse(dataEl.textContent.trim());
    } catch (err) {
        console.error("Failed to parse charts JSON:", err);
        return;
    }

    console.log("Income vs Expense raw data:", chartsData);

    // Use the first object directly
    const chartObj = chartsData[0];

    const canvas = document.getElementById("incomeexpenses-bar");
    if (!canvas) return console.warn("No canvas found for Income vs Expense");
    const ctx = canvas.getContext("2d");

    canvas._chartInstance?.destroy();

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: chartObj.labels,   // ["Income", "Expense"]
            datasets: [{
                label: "Total",
                data: chartObj.data,   // [incometotal, expensetotal]
                backgroundColor: ["#1dd1a1", "#ff6b6b"]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: value => "$" + value }
                }
            }
        }
    });
});
