document.addEventListener("DOMContentLoaded", () => {

    const dataScript = document.getElementById("charts-data");

    const raw = dataScript.textContent && dataScript.textContent.trim();

    let chartsData;
    try {
        chartsData = JSON.parse(raw);
    } catch (err) {
        console.error("❌ Failed to parse charts JSON:", err, raw);
        return;
    }

    // GENERATE COLOR PALETTE OF N COLORS
    function makeColors(n) {
        const base = [235, 22, 22]; // red-ish base
        const colors = [];
        for (let i = 0; i < n; i++) {
            // VARY ALPHA AND SHIFT HUE BY i
            const alpha = 0.85 - (i * 0.12);
            colors.push(`rgba(${base[0]}, ${Math.max(base[1] - i * 2, 10)}, ${Math.max(base[2] - i * 1, 10)}, ${Math.max(alpha, 0.08)})`);
        }
        return colors;
    }

    // ITERATE AND CREATE CHARTS
    chartsData.forEach((chartObj, index) => {

        // MATCHING CANVAS
        const canvasId = `doughnut${index + 1}`;
        const canvas = document.getElementById(canvasId);

        // ENSURE NUMBER VALUE
        const numericData = chartObj.data.map(v => {
            const n = Number(v);
            return Number.isFinite(n) ? n : 0;
        });

        // IF ZERO, ADD A ZERO SINGLE SLICE PIE
        const sum = numericData.reduce((a, b) => a + b, 0);
        let dataToPlot = numericData;
        let labelsToPlot = chartObj.labels.slice();
        if (sum === 0) {
            labelsToPlot = ["No data"];
            dataToPlot = [1]; // SMALL SLICE FOR 0
        }

        // COLORS MATCH LENGTH
        const colors = makeColors(dataToPlot.length);

        // DESTROY PREVIOUS CHART INSTANCE
        if (canvas._activeChart instanceof Chart) {
            try { canvas._activeChart.destroy(); } catch (e) { /* IGNORE */ }
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
            // STORE REFERENCE TO DESTROY LATER IF NEEDED
            canvas._activeChart = chartInstance;
        } catch (err) {
            console.error(`Failed to render chart ${index + 1}:`, err);
        }
    });
});
