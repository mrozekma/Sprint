$(document).ready(function() {
	$('select').chosen();
	$('input.date').datepicker({
		beforeShowDay: $.datepicker.noWeekends
	});

	flag_private = $('#flag-private');
	flag_hidden = $('#flag-hidden');
	flag_hidden.change(function() {
		if(flag_hidden.prop('checked')) {
			flag_private.data('old', flag_private.prop('checked')).prop('checked', true).prop('disabled', true);
		} else {
			flag_private.prop('checked', flag_private.data('old')).prop('disabled', false);
		}
	});

	$('#save-button').savebutton($('#post-status'), '');
	$('#cancel-button').cancelbutton('/');
});
