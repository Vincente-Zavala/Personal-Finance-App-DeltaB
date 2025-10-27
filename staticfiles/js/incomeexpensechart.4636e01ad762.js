// Doughnut Chart
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


    // === 3️⃣ Render a single chart ===
    function renderChart(type, chartObj) {
        const canvas = document.getElementById(`incomeexpensevs-${type.toLowerCase()}`);
        if (!canvas) {
            console.warn(`No canvas found for "${type}"`);
            return;
        }

        const incomeexpense = canvas.getContext("2d");

        var myChart2 = new Chart(incomeexpense, {
            type: "bar",
            data: {
                datasets: [{
                    label: chartObj.labels,
                    data: chartObj.data,
                    backgroundColor: "rgba(235, 22, 22, .7)",
                    fill: true
                },
                {
                    label: chartObj.labels,
                    data: chartObj.data,
                    backgroundColor: "rgba(235, 22, 22, .5)",
                    fill: true
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

    }


    // === Render all charts ===
    chartsData.forEach((chartObj) => {
        renderChart(chartObj.type, chartObj);
    });
          
});