document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('billCalendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      height: 'auto',
      themeSystem: 'bootstrap5',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,listWeek'
      },
      events: '/get-bills/', // Django view endpoint returning bills
      dateClick: function(info) {
        alert('Clicked on: ' + info.dateStr);
      },
      eventClick: function(info) {
        alert('Bill: ' + info.event.title + '\nDue: ' + info.event.start.toISOString().split("T")[0]);
      }
    });

    calendar.render();
  });