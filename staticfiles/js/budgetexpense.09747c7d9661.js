document.addEventListener("DOMContentLoaded", () => {

    const dataEl = document.getElementById("budgetexpense-chart-data");
    const chartData = JSON.parse(dataEl.textContent);

    console.log(chartData);


    
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "This Month",
                data: data,
                backgroundColor: [
                    "#1dd1a1", "#ff6b6b", "#feca57", "#54a0ff",
                    "#5f27cd", "#48dbfb", "#00d2d3", "#576574"
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                title: { display: true, text: "Category Totals vs Budget Limit" }
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
