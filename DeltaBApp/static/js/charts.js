document.addEventListener("DOMContentLoaded", () => {
    const dataEl = document.getElementById("charts-data");
    if (!dataEl) return console.error("No charts-data element found.");
  
    let chartsData;
    try {
      chartsData = JSON.parse(dataEl.textContent.trim());
    } catch (err) {
      console.error("Failed to parse charts JSON:", err);
      return;
    }
  
    chartsData.forEach((obj, i) => console.log(`Chart ${i}:`, obj));


    const makeColors = (n) => {
      const palette = [
        "#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd",
        "#ff9f43", "#ee5253", "#10ac84", "#341f97", "#c8d6e5"
      ];
      return Array.from({ length: n }, (_, i) => palette[i % palette.length]);
    };


    function renderChart(type, chartObj) {
      console.warn("Type", type);
      const canvas = document.getElementById(`chart-${type.toLowerCase()}`);
      if (!canvas) {
        console.warn(`No canvas found for "${type}"`);
        return;
      }
  
      const ctx = canvas.getContext("2d");
      const colors = makeColors(chartObj.data.length);
  
      if (canvas._chartInstance instanceof Chart) {
        canvas._chartInstance.destroy();
      }

      console.warn(`Data`, chartObj.data);


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
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "top" },
          }
        }
      });
    }
  
    chartsData.forEach((chartObj) => {
      renderChart(chartObj.type, chartObj);
    });
  

    window.renderChartByType = function (typeName) {
      const chartObj = chartsData.find(
        (obj) => obj.type.toLowerCase() === typeName.toLowerCase()
      );
      if (!chartObj) return console.error(`No chart found for "${typeName}"`);
      renderChart(typeName, chartObj);
    };
  });
  