$(document).ready(function() {
	$('table.availability tr.dateline button').click(function() {
		$('table.availability tr.userline td input').val('8');
		return false;
	});

	$('table.availability tr.userline button').click(function() {
		row = $(this).parents('tr');
		hours = $('td:eq(1) input', row).val();
		$('td:gt(1) input', row).val(hours);
		return false;
	});

	$('#save-button').savebutton($('#post-status'), '/sprints/' + sprintid);
});
