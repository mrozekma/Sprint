$(document).ready(function() {
	$('table.availability tr.dateline button').click(function() {
		$('table.availability tr.userline td input').val('8');
		return false;
	});

	copyDown = $('table.availability tr.dateline td.buttons img');
	copyDown.click(function() {
		index = copyDown.index($(this));
		hours = $('tr.userline:eq(0) input:eq(' + index + ')').val();
		$('tr.userline').each(function() {
			$('input:eq(' + index + ')', this).val(hours);
		});
		return false;
	});

	copyRight = $('table.availability tr.userline td.buttons img');
	copyRight.click(function() {
		row = $(this).parents('tr');
		hours = $('input:eq(0)', row).val();
		$('input', row).val(hours);
		return false;
	});

	$('#save-button,#save-button2').savebutton($('#post-status'), '/sprints/' + sprintid);
});
