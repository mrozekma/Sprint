$(document).ready(function() {
	$('select').chosen();

	// Remove all closed tasks from the list
	$('tr.task').filter('[status="canceled"],[status="complete"],[status="split"]').remove();

	// Remove groups with no tasks
	$('tr.group').each(function() {
		groupid = $(this).attr('groupid');
		if($('tr.task[groupid="' + groupid + '"]').length == 0) {
			$(this).remove();
		}
	});

	$('#save-button').click(function(e) {
		e.preventDefault();
		e.stopImmediatePropagation();
		box = $('#post-status');

		data = []
		$('tr.task input:checked').each(function() {
			task = $(this).parents('tr.task');
			data.push({
				name: $('td.name span', task).text(),
				assigned: task.attr('assigned'),
				status: task.attr('status'),
				groupid: parseInt(task.attr('groupid'), 10),
				hours: parseInt($('td.hours input[type="text"]', task).val(), 10)
			});
		});

		console.log('what the hell');
		$.post(post_url, {data: JSON.stringify(data)}, function(data, text, request) {
			switch(request.status) {
			case 200:
				box.attr('class', 'alert-message error');
				$('span.boxbody', box).html(data);
				break;
			case 298:
				box.attr('class', 'alert-message warning');
				$('span.boxbody', box).html(data);
				break;
			case 299:
				window.location = next_url;
				return;
			default:
				box.attr('class', 'alert-message error');
				$('span.boxbody', box).html("Unexpected response code " + request.status)
				break;
			}

			showbox(box);
		});
	});
	if(typeof(next_url) !== 'undefined') {
		$('#cancel-button').cancelbutton(next_url);
	}
});
