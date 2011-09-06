$(document).ready(function() {
	$('select').multiselect({
		noneSelectedText: "Select sprints to export",
		selectedText: function(num, total, selected) {return num + (num == 1 ? " sprint" : " sprints") + " selected";}
	});

	$('img.format:first').addClass('selected');

	$('img.format').click(function() {
		selected = $(this);
		$('img.format.selected').effect('transfer', {to: selected}, 300, function() {selected.addClass('selected');});
		$('img.format.selected').removeClass('selected');
		$('#export-button').attr('disabled', true);
		console.log($('#export-button').attr('disabled'));
	});

	$('#export-button').click(function() {
		if($('img.format.selected').length == 0) {return;}
		sprints = $('select option:selected').map(function() {return $(this).attr('value');}).get().join(',');
		document.location = '/sprints/export/render?sprints=' + sprints + '&format=' + $('img.format.selected').attr('export-name');
	});
});
