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

    chartsData.forEach((obj, i) => console.log(`Chart ${i}:`, obj));


    // === 3️⃣ Render a single chart ===
    function renderIncomeExpenseChart(type, chartObj) {
        console.warn("Type", type);
        const canvas = document.getElementById("incomeexpenses-bar");
        if (!canvas) {
            console.warn(`No canvas found for Income vs Expense`);
            return;
        }

        const ctx = canvas.getContext("2d");

        // Destroy existing chart instance
        if (canvas._chartInstance instanceof Chart) {
            canvas._chartInstance.destroy();
        }

        console.warn(`Data`, chartObj.data);

        canvas._chartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: chartObj.labels,
                datasets: [{
                    label: "Total",
                    data: chartObj.data,
                    backgroundColor: ["#1dd1a1", "#ff6b6b"],
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
                        ticks: {
                            callback: function(value) { return "$" + value; }
                        }
                    }
                }
            }
        });
    }


    // === Render Chart ===
    if (chartsData.length > 0) {
        renderIncomeExpenseChart(chartsData[0]);
    }
});