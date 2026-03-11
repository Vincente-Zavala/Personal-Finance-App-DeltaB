document.addEventListener("DOMContentLoaded", () => {

    const dataEl = document.getElementById("budgetexpense-chart-data");
    const chartData = JSON.parse(dataEl.textContent);

    // Extract labels and datasets
    const labels = chartData.map(d => d.category);
    const spentData = chartData.map(d => d.spent);
    const budgetData = chartData.map(d => d.budget);

    const ctx = document.getElementById("budgetexpense-bar").getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Received/Spent",
                    data: spentData,
                    backgroundColor: "#ff6b6b"
                },
                {
                    label: "Budget",
                    data: budgetData,
                    backgroundColor: "#1dd1a1"
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true },
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
