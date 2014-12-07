$(document).ready(function() {
	$('input.date[name=start]').datepicker({
		minDate: startMin,
		beforeShowDay: $.datepicker.noWeekends
	});
	$('input.date[name=end]').datepicker({
		minDate: endMin,
		beforeShowDay: $.datepicker.noWeekends
	});

	$('input[type=text].goal').each(function() {
		$(this).data('old', $(this).val());
		$(this).bind('propertychange.chg keyup.chg input.chg paste.chg', function() {
			if($(this).data('old') != $(this).val()) {
				$(this).unbind('.chg');
				$('#clear-tasks-' + $(this).attr('goalid')).show();
			}
		});
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

	$('select').chosen();
	$('#save-button').savebutton($('#post-status'), '/sprints/' + sprintid);
});
