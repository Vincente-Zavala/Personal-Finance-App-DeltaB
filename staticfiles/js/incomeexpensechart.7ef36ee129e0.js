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

    // Calculate totals
    const incomeObj = chartsData.find(c => c.type.toLowerCase() === "income");
    const expenseObj = chartsData.find(c => c.type.toLowerCase() === "expense");

    const incomeTotal = incomeObj ? incomeObj.data.reduce((a, b) => a + b, 0) : 0;
    const expenseTotal = expenseObj ? expenseObj.data.reduce((a, b) => a + b, 0) : 0;

    console.log("Income total:", incomeTotal, "Expense total:", expenseTotal);

    const chartData = {
        labels: ["Income", "Expense"],
        data: [incomeTotal, expenseTotal]
    };

    // Render chart
    const canvas = document.getElementById("incomeexpenses-bar");
    if (!canvas) return console.warn("No canvas found for Income vs Expense");
    const ctx = canvas.getContext("2d");

    canvas._chartInstance?.destroy();

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: chartData.labels,
            datasets: [{
                label: "Total",
                data: chartData.data,
                backgroundColor: ["#1dd1a1", "#ff6b6b"]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true },
                title: { display: true, text: "Income vs Expense" }
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
