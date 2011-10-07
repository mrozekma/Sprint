$(document).ready(function() {
	$('select').chosen();
	$('input.date').datepicker();

	$('#save-button').savebutton($('#post-status'), '');
	$('#cancel-button').cancelbutton();
});
