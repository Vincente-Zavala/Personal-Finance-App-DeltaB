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

      events: [
        {
          title: 'Pay Rent',
          start: '2025-10-30',
          color: '#dc3545' // red badge color
        },
        {
          title: 'Car Insurance',
          start: '2025-11-03',
          color: '#0d6efd'
        }],
        
      selectable: true,
        select: function(info) {
          alert('Selected: ' + info.startStr + ' to ' + info.endStr);
        },
    
        eventClick: function(info) {
          alert('Clicked on: ' + info.event.title);
        }
    });
  
    calendar.render();
  });
  