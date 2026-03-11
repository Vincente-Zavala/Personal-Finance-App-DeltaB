document.addEventListener("DOMContentLoaded", function () {

  const fromPicker = flatpickr("#fromdate", {
    dateFormat: "m-d-Y",
    allowInput: true
  });

  const toPicker = flatpickr("#todate", {
    dateFormat: "m-d-Y",
    allowInput: true
  });

  const inputPicker = flatpickr("#inputdate", {
    dateFormat: "m-d-Y",
    allowInput: true
  });

  window.setPreset = function (type) {
    const today = new Date();
    let from, to;

    if (type === "last7") {
      to = new Date(today);
      from = new Date(today);
      from.setDate(today.getDate() - 6);
    }

    if (type === "thismonth") {
      from = new Date(today.getFullYear(), today.getMonth(), 1);
      to = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    }

    if (type === "lastmonth") {
      from = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      to = new Date(today.getFullYear(), today.getMonth(), 0);
    }
    
    if (type === "yeartodate") {
      from = new Date(today.getFullYear(), 0, 1);
      to = new Date(today);
    }

    if (from && to) {
      fromPicker.setDate(from, true);
      toPicker.setDate(to, true);
    }
  };
});
