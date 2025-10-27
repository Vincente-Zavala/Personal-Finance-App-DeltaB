document.addEventListener("DOMContentLoaded", () => {
    // === 1️⃣ Parse chart data from HTML ===
    const dataEl = document.getElementById("charts-data");
    if (!dataEl) return console.error("No charts-data element found.");
  
    let chartsData = [];
    try {
      chartsData = JSON.parse(dataEl.textContent.trim());
    } catch (err) {
      console.error("Failed to parse charts JSON:", err);
      return;
    }
  
    // === 2️⃣ Helper: Generate color palette ===
    const makeColors = (n) => {
      const palette = [
        "#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd",
        "#ff9f43", "#ee5253", "#10ac84", "#341f97", "#c8d6e5"
      ];
      return Array.from({ length: n }, (_, i) => palette[i % palette.length]);
    };
  
    // === 3️⃣ Helper: Create a chart ===
    function renderChart(canvasId, chartObj) {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return console.warn(`Canvas "${canvasId}" not found.`);
  
      const { labels, data, type } = chartObj;
      const colors = makeColors(data.length);
      const ctx = canvas.getContext("2d");
  
      if (canvas._chartInstance instanceof Chart) {
        canvas._chartInstance.destroy();
      }
  
      canvas._chartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [{ data, backgroundColor: colors }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: "top" },
            title: { display: true, text: `${type} by Category` }
          }
        }
      });
    }
  
    // === 4️⃣ Auto-generate all charts dynamically ===
    const container = document.getElementById("charts-container");
  
    chartsData.forEach((chartObj) => {
      const chartId = `chart-${chartObj.type.toLowerCase()}`;
      container.appendChild(chartBox);
      renderChart(chartId, chartObj);
    });
  
    // === 5️⃣ Expose global helper to render one specific chart ===
    window.renderChartByType = function (typeName) {
      const chartObj = chartsData.find(
        (obj) => obj.type.toLowerCase() === typeName.toLowerCase()
      );
      if (!chartObj) return console.error(`No chart found for "${typeName}"`);
      const chartId = `chart-${typeName.toLowerCase()}`;
      renderChart(chartId, chartObj);
    };
  });
  