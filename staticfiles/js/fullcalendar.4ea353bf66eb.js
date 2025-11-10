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

  // 🎨 Inject the correct color per category type
  const coloredEvents = remindersData.map(event => {
    const type = event.categoryType?.toLowerCase()?.trim();
    const style = categoryTypeStyles[type];
    return {
      ...event,
      backgroundColor: style ? style.color : "#0c0c0c",
      borderColor: style ? style.color : "#0c0c0c",
      textColor: "#fff",
    };
  });

  // 🗓️ Initialize FullCalendar
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    events: coloredEvents,
    eventDidMount: function(info) {
      // Optional glow accent
      const color = info.event.backgroundColor;
      info.el.style.boxShadow = `0 0 8px ${color}`;
    },
  });

  calendar.render();
});
