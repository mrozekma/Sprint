var distMin = 40, distMax = 80;
var distData = undefined;
var errorMessage = undefined;

$(document).ready(function() {
	$('#distribution-range-slider').slider({
		range: true,
		min: 0,
		max: 100,
		step: 5,
		values: [distMin, distMax],
		slide: function(event, ui) {
			distMin = ui.values[0];
			distMax = ui.values[1];
			updateDistSpan();
			process();
		}
	});

	$('.task-distribution img.user-gravatar').click(function() {
		update($(this).parents('.task-distribution').attr('userid'));
	});

	updateDistSpan(distMin, distMax);
	update();
});

function update(target_userid) {
	data = {'sprint': sprintid};
	if(target_userid != undefined) {
		data['targetUser'] = target_userid;
		data['tasks'] = $.makeArray($('select.tasks :selected').map(function() {return $(this).val();})).join(',');
	}

	$.ajax({
		url: '/tasks/distribute/update',
		type: 'POST',
		data: data,
		success: function(data, text, request) {
			distData = data;
			errorMessage = distData.error;
			process();
		},
		error: function(request, text, errorThrown) {
			distData = undefined;
			errorMessage = text + ' - ' + errorThrown;
		}
	});
}

function updateDistSpan() {
	$('#distribution-range span').text(distMin + '% - ' + distMax + '%');
}

function process() {
	if(errorMessage != undefined) {
		box = $('#post-status');
		box.attr('class', 'alert-message error');
		$('span.boxbody', box).html(errorMessage);
		showbox(box);
		return;
	}
	$('#post-status').hide();
	if(distData == undefined) {return;}

	for(userid in distData) {
		user = distData[userid];
		pcnt = user.availability == 0 ? (user.hours > 0 ? 101 : 100) : Math.floor(user.hours * 100 / user.availability);

		box = $('.task-distribution[userid=' + userid + ']');
		sel = $('select.tasks', box);

		$('.hours', box).html(user.hours + ' / ' + user.availability + ' hours (' + user.tasks.length + (user.tasks.length == 1 ? ' task' : ' tasks') + ', ' + (user.availability == 0 && user.hours > 0 ? '&#8734;' : pcnt) + '%)');
		$('.task-progress-total .progress-current', box).css('width', Math.min(100, pcnt) + '%').css('visibility', pcnt > 0 ? 'visible' : 'hidden').toggleClass('progress-current-red', pcnt < distMin || pcnt > distMax);

		sel.html('');
		for(i in user.tasks) {
			task = user.tasks[i];
			sel.append($('<option/>').val(task.id).text(task.text));
		}
	}
}