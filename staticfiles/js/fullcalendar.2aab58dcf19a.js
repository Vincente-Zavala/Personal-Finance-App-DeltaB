document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('billCalendar');
  
    if (!calendarEl) {
      console.error("Calendar container not found.");
      return;
    }
  
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      height: 'auto',
      themeSystem: 'standard',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
    });
  
    calendar.render();
  });
  