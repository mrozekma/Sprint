$(document).ready(function() {
	$('select').multiselect({
		noneSelectedText: "Select sprints to export",
		selectedText: function(num, total, selected) {return num + (num == 1 ? " sprint" : " sprints") + " selected";}
	});

	$('img.format:first').addClass('selected');

	animating = false;
	$('img.format').click(function() {
		selected = $(this);
		animating = true;
		$('img.format.selected').effect('transfer', {to: selected}, 300, function() {
			selected.addClass('selected');
			animating = false;
		});
		$('img.format.selected').removeClass('selected');
	});

	$('#export-button').click(function() {
		if(animating) {return;}
		if($('img.format.selected').length == 0) {return;}
		sprints = $('select option:selected').map(function() {return $(this).attr('value');}).get().join(',');
		document.location = '/sprints/export/render?sprints=' + sprints + '&format=' + $('img.format.selected').attr('export-name');
	});
});
