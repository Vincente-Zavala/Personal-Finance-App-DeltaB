document.addEventListener("DOMContentLoaded", () => {
    // === 1️⃣ Load chart data ===
    const dataEl = document.getElementById("savingstransaction-chart-data");
    if (!dataEl) return console.error("No charts-data element found.");
  
    let chartsData;
    try {
      chartsData = JSON.parse(dataEl.textContent.trim());
    } catch (err) {
      console.error("Failed to parse charts JSON:", err);
      return;
    }
  
    chartsData.forEach((obj, i) => console.log(`Chart ${i}:`, obj));


    // === 3️⃣ Render a single chart ===
    function renderChart(chartObj) {
      console.warn("Type", type);
      const canvas = document.getElementById("savingstransaction-line");
      if (!canvas) {
        console.warn(`No canvas found for Savings Line`);
        return;
      }
  
      const ctx = canvas.getContext("2d");
  
      // Destroy existing chart instance
      if (canvas._chartInstance instanceof Chart) {
        canvas._chartInstance.destroy();
      }

      console.warn(`Data`, chartObj.data);

      canvas._chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: chartObj.date,
            datasets: [{
                fill: true,
                backgroundColor: "rgba(235, 22, 22, .7)",
                data: chartObj.data
            }]
        },
        options: {
            responsive: true
        }
      });
    }
  
  });
  