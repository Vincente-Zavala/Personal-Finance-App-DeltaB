// Doughnut Chart
document.addEventListener("DOMContentLoaded", () => {

    var incomeexpense = document.getElementById("income-expense").getContext("2d");

    var myChart2 = new Chart(incomeexpense, {
        type: "line",
        data: {
            labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
            datasets: [
                {
                    label: "Income",
                    data: [3000, 3200, 2800, 3500, 3700, 3600, 3900],
                    backgroundColor: "rgba(40, 167, 69, 0.4)",
                    borderColor: "rgba(40, 167, 69, 1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: "Expense",
                    data: [2200, 2500, 2600, 2400, 2700, 2900, 3000],
                    backgroundColor: "rgba(220, 53, 69, 0.4)",
                    borderColor: "rgba(220, 53, 69, 1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "top" },
                title: { display: true, text: "Income vs Expense" }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return "$" + value;
                        }
                    }
                }
            }
        }
    });
});