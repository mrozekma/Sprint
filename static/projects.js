$(document).ready(function() {
	$('#calendar').fullCalendar({
		events: '/api/sprints/list',
		weekends: false,
		eventClick: function(event, jsEvent, view) {
			document.location = '/sprints/' + event.id
		}
	});

	// This is a hack to shove a List button into the calendar's navigation panel
	btn = $('<span class="fc-button fc-state-default fc-corner-left fc-corner-right" style="margin-right: 10px"><span class="fc-button-inner"><span class="fc-button-content">list</span></span></span>');
	btn.click(function() {document.location = '/';});
	$('.fc-header-right').prepend(btn);
});
