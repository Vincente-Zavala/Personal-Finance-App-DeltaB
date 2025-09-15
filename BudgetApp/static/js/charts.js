document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ charts.js loaded");

    const dataScript = document.getElementById("charts-data");
    if (!dataScript) {
        console.warn("⚠️ No #charts-data element found on page.");
        return;
    }

    const raw = dataScript.textContent && dataScript.textContent.trim();
    if (!raw) {
        console.warn("⚠️ #charts-data is empty.");
        return;
    }

    let chartsData;
    try {
        chartsData = JSON.parse(raw);
    } catch (err) {
        console.error("❌ Failed to parse charts JSON:", err, raw);
        return;
    }

    console.log("chartsData from Django:", chartsData);

    // helper to generate color palette of N colors (variations in alpha)
    function makeColors(n) {
        const base = [235, 22, 22]; // red-ish base
        const colors = [];
        for (let i = 0; i < n; i++) {
            // vary alpha and slightly shift hue using i
            const alpha = 0.85 - (i * 0.12);
            colors.push(`rgba(${base[0]}, ${Math.max(base[1] - i * 2, 10)}, ${Math.max(base[2] - i * 1, 10)}, ${Math.max(alpha, 0.08)})`);
        }
        return colors;
    }

    // iterate and create charts
    chartsData.forEach((chartObj, index) => {
        console.log(`Preparing chart ${index + 1}:`, chartObj);

        // validate
        if (!chartObj || !Array.isArray(chartObj.labels) || !Array.isArray(chartObj.data)) {
            console.warn(`Chart ${index + 1} skipped: invalid chart object`, chartObj);
            return;
        }

        // find matching canvas
        const canvasId = `doughnut${index + 1}`;
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`Canvas #${canvasId} not found for chart ${index + 1}.`);
            return;
        }

        // ensure numeric values
        const numericData = chartObj.data.map(v => {
            const n = Number(v);
            return Number.isFinite(n) ? n : 0;
        });

        // if all zeros -> optionally draw a single "No data" slice so it isn't invisible
        const sum = numericData.reduce((a, b) => a + b, 0);
        let dataToPlot = numericData;
        let labelsToPlot = chartObj.labels.slice();
        if (sum === 0) {
            console.warn(`Chart ${index + 1} (${chartObj.type}) has all-zero data. Chart will show an "No data" slice.`);
            labelsToPlot = ["No data"];
            dataToPlot = [1]; // small visible slice
        }

        // ensure colors match length
        const colors = makeColors(dataToPlot.length);

        // destroy previous Chart instance if present (in case of hot reloads)
        if (canvas._activeChart instanceof Chart) {
            try { canvas._activeChart.destroy(); } catch (e) { /* ignore */ }
        }

        const ctx = canvas.getContext("2d");
        const cfg = {
            type: "doughnut",
            data: {
                labels: labelsToPlot,
                datasets: [{
                    data: dataToPlot,
                    backgroundColor: colors
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                    },
                    legend: {
                        position: "top"
                        
                    }
                }
            }
        };

        try {
            const chartInstance = new Chart(ctx, cfg);
            // store reference to later destroy if needed
            canvas._activeChart = chartInstance;
            console.log(`Chart ${index + 1} rendered (${canvasId}).`);
        } catch (err) {
            console.error(`Failed to render chart ${index + 1}:`, err);
        }
    });
});
