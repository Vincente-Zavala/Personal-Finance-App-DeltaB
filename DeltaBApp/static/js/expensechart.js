document.addEventListener("DOMContentLoaded", () => {

    const dataScript = document.getElementById("expense-chart-data");
    if (!dataScript) return;

    const data = JSON.parse(dataScript.textContent);

    var xValues = ["Italy", "France", "Spain", "USA", "Argentina"];
    var barColors = [
        "rgba(235, 22, 22, .7)",
        "rgba(235, 22, 22, .6)",
        "rgba(235, 22, 22, .5)",
        "rgba(235, 22, 22, .4)",
        "rgba(235, 22, 22, .3)"
    ];

    new Chart("expensedoughnut", {
    type: "doughnut",
    data: {
        labels: xValues,
        datasets: [{
        backgroundColor: barColors,
        data: data
        }]
    },
    options: {
        title: {
        display: true,
        text: "World Wide Wine Production 2018"
        }
    }
    });

});