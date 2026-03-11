document.addEventListener("DOMContentLoaded", function() {
  const categoryTypeStyles = {
    income: { color: "#38EB14", icon: "fa-arrow-trend-up" },
    expense: { color: "#EB1616", icon: "fa-arrow-trend-down" },
    savings: { color: "#1443EB", icon: "fa-piggy-bank" },
    transfer: { color: "#9CA3AF", icon: "fa-right-left" },
    debt: { color: "#EB8314", icon: "fa-file-invoice-dollar" },
    investment: { color: "#EB14A0", icon: "fa-chart-line" },
    refund: { color: "#8B5CF6", icon: "fa-rotate-left" },
    reimbursement: { color: "#8B5CF6", icon: "fa-rotate-left" },
    retirement: { color: "#FFD700", icon: "fa-umbrella-beach" },
  };

  const calendarEl = document.getElementById("billCalendar");
  const remindersData = JSON.parse(
    document.getElementById("reminders-data").textContent
  );

  const coloredEvents = remindersData.map(event => {
    const type = event.categoryType?.toLowerCase()?.trim();
    const style = categoryTypeStyles[type];

    return {
      ...event,
      backgroundColor: "var(--bs-dark)",
      borderColor: style ? style.color : "#0c0c0c",
      textColor: style ? style.color : "#fff",
      styleColor: style ? style.color : "#fff",
    };
  });

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    events: coloredEvents,

    eventContent: function(info) {
      const color = info.event.extendedProps.styleColor;
      const amount = info.event.extendedProps.amount;
      const name = info.event.extendedProps.name;

      // Compact, minimal layout
      const innerHtml = `
        <div style="
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.75rem;
          line-height: 1.1;
          padding: 2px 4px;
          color: ${color};
          font-weight: 600;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        ">
          <span style="flex: 1; overflow: hidden; text-overflow: ellipsis;">
            ${name}
          </span>
          <span style="color: white; font-weight: 500; margin-left: 6px;">
            $${amount}
          </span>
        </div>
      `;

      return { html: innerHtml };
    },

    eventDidMount: function(info) {
      const color = info.event.borderColor;
      info.el.style.setProperty("border", `1px solid ${color}`, "important");
      info.el.style.setProperty("background-color", "var(--bs-dark)", "important");
      info.el.style.setProperty("border-radius", "6px", "important");
      info.el.style.setProperty("padding", "0", "important");
      info.el.style.setProperty("margin", "1px 0", "important");
    },
  });

  calendar.render();
});
