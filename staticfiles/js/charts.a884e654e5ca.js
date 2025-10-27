document.addEventListener("DOMContentLoaded", () => {
    // === 1️⃣ Load chart data ===
    const dataEl = document.getElementById("charts-data");
    if (!dataEl) return console.error("No charts-data element found.");
  
    let chartsData;
    try {
      chartsData = JSON.parse(dataEl.textContent.trim());
    } catch (err) {
      console.error("Failed to parse charts JSON:", err);
      return;
    }
  
    // === 2️⃣ Helper: Color palette ===
    const makeColors = (n) => {
      const palette = [
        "#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd",
        "#ff9f43", "#ee5253", "#10ac84", "#341f97", "#c8d6e5"
      ];
      return Array.from({ length: n }, (_, i) => palette[i % palette.length]);
    };
  
    // === 3️⃣ Render a single chart ===
    function renderChart(type, chartObj) {
      const canvas = document.getElementById(`chart-${type.toLowerCase()}`);
      if (!canvas) {
        console.warn(`No canvas found for "${type}"`);
        return;
      }
  
      const ctx = canvas.getContext("2d");
      const colors = makeColors(chartObj.data.length);
  
      // Destroy existing chart instance
      if (canvas._chartInstance instanceof Chart) {
        canvas._chartInstance.destroy();
      }

      console.warn(`Data "${data}"`);

      canvas._chartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: chartObj.labels,
          datasets: [{
            data: chartObj.data,
            backgroundColor: colors
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: "top" },
            title: { display: true, text: `${chartObj.type} by Category` }
          }
        }
      });
    }
  
    // === 4️⃣ Render all charts ===
    chartsData.forEach((chartObj) => {
      renderChart(chartObj.type, chartObj);
    });
  
    // === 5️⃣ Optional: expose helper to render one manually ===
    window.renderChartByType = function (typeName) {
      const chartObj = chartsData.find(
        (obj) => obj.type.toLowerCase() === typeName.toLowerCase()
      );
      if (!chartObj) return console.error(`No chart found for "${typeName}"`);
      renderChart(typeName, chartObj);
    };
  });
  