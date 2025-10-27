document.addEventListener("DOMContentLoaded", () => {

    var xValues = ["Italy", "France", "Spain", "USA", "Argentina"];
    var yValues = [55, 49, 44, 24, 15];
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
        data: yValues
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