document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('billCalendar');
  
    if (!calendarEl) {
      console.error("No element found with id='billCalendar'");
      return;
    }
  
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      height: 'auto',
      themeSystem: 'bootstrap5',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,listWeek'
      },
      events: [], // no data yet
    });
  
    calendar.render();
  });
  