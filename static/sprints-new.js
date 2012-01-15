$(document).ready(function() {
	$('select').chosen();
	$('input.date').datepicker({
		beforeShowDay: $.datepicker.noWeekends
	});

	$('#save-button').savebutton($('#post-status'), '');
	$('#cancel-button').cancelbutton('/');
});
