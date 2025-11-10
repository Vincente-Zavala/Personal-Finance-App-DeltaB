document.addEventListener("DOMContentLoaded", function() {
  const categoryTypeStyles = {
    income: { color: "#38EB14", icon: "fa-arrow-trend-up" },
    expense: { color: "#EB1616", icon: "fa-arrow-trend-down" },
    savings: { color: "#1443EB", icon: "fa-piggy-bank" },
    transfer: { color: "#9CA3AF", icon: "fa-right-left" },
    debt: { color: "#EB8314", icon: "fa-file-invoice-dollar" },
    investment: { color: "#EB14A0", icon: "fa-chart-line" },
    refund: { color: "#8B5CF6", icon: "fa-rotate-left" },
    retirement: { color: "#FFD700", icon: "fa-umbrella-beach" },
  };

  const calendarEl = document.getElementById("billCalendar");

  // 🧩 Parse reminders from script tag
  const remindersData = JSON.parse(
    document.getElementById("reminders-data").textContent
  );

  // 🎨 Apply text and border color only
  const coloredEvents = remindersData.map(event => {
    const type = event.categoryType?.toLowerCase()?.trim();
    const style = categoryTypeStyles[type];
    return {
      ...event,
      backgroundColor: "transparent", // keep background transparent
      borderColor: style ? style.color : "#0c0c0c", // border = type color
      textColor: style ? style.color : "#fff", // text = type color
    };
  });

  // 🗓️ Initialize FullCalendar
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    events: coloredEvents,
    eventDidMount: function(info) {
      // Ensure border + text color are consistent
      const color = info.event.borderColor;
      info.el.style.border = `2px solid ${color}`;
      info.el.style.color = color;
      info.el.style.background = "transparent";
    },
  });

  calendar.render();
});
