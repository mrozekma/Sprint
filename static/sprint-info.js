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

	$('select').chosen();
	$('#save-button').savebutton($('#post-status'), '/sprints/' + sprintid);
});
