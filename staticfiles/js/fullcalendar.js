document.addEventListener("DOMContentLoaded", function() {
  const calendarEl = document.getElementById("billCalendar");
  if (!calendarEl) return;

  // Read the reminders from the JSON script tag
  const remindersDataScript = document.getElementById("reminders-data");
  const remindersData = remindersDataScript
    ? JSON.parse(remindersDataScript.textContent)
    : [];

  // Initialize FullCalendar
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    height: "auto",
    themeSystem: "standard",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay"
    },
    events: remindersData, // use the parsed data
    selectable: true,
    select(info) {
      alert('Selected: ' + info.startStr + ' to ' + info.endStr);
    },
    eventClick(info) {
      alert('Clicked on: ' + info.event.title);
    }
  });

  calendar.render();
});
