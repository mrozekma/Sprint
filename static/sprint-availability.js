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

	$('#save-button').click(function(e) {
		e.preventDefault();
        e.stopImmediatePropagation();
		$.post($('form').attr('action'), $('form').serialize(), function(data, text, request) {
			box = $('#post-status')
			switch(request.status) {
			case 200:
				box.attr('class', 'tint red');
				$('span', box).html(data);
				break;
			case 298:
				box.attr('class', 'tint yellow');
				$('span', box).html(data);
				break;
			case 299:
				document.location = '/sprints/' + sprintid;
				return;
			default:
				box.attr('class', 'tint blood');
				$('span', box).html("Unexpected response code " + request.status)
				break;
			}

			box.fadeIn();
		});
	});
});
