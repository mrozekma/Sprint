$(document).ready(function() {
	$('select:not([disabled])').chosen();
	$('#save-button').savebutton($('#post-status'), '');
	$('#cancel-button').cancelbutton(next_url);
});
