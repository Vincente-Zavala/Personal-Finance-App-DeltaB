document.addEventListener("DOMContentLoaded", () => {
    const dataEl = document.getElementById("savingstransaction-chart-data");
    if (!dataEl) return console.error("No savings chart data element found.");
  
    let savingsData;
    try {
      savingsData = JSON.parse(dataEl.textContent.trim());
    } catch (err) {
      console.error("Failed to parse savings JSON:", err);
      return;
    }
  
    console.log("Savings Data:", savingsData);
  
    const canvas = document.getElementById("savingstransaction-line");
    if (!canvas) {
      console.error("Canvas not found for savings chart.");
      return;
    }
  
    const ctx = canvas.getContext("2d");
  
    new Chart(ctx, {
      type: "line",
      data: {
        labels: savingsData.labels,
        datasets: [{
          label: "Savings Over Time",
          data: savingsData.data,
          borderColor: "rgba(235, 22, 22, 1)",
          backgroundColor: "rgba(235, 22, 22, 0.2)",
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            title: { display: true, text: "Date" }
          },
          y: {
            title: { display: true, text: "Amount ($)" },
            beginAtZero: true
          }
        }
      }
    });
  });
  