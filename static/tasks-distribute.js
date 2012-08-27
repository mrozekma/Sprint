var distMin = 40, distMax = 80;
var distData = undefined;
var errorMessage = undefined;
var userLeft = undefined, userRight = undefined;

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

	$('.distribution img.user-gravatar').click(function() {
		col = $(this).parents('.distribution');
		side = col.hasClass('left') ? 'left' : 'right';
		$(this).effect('transfer', {
			to: '.distribution.' + side + ' .selected img.user-gravatar',
			className: 'distribution-transfer'
		}, 'fast', function() {
			if(side == 'left') {
				userLeft = $(this).attr('userid');
			} else {
				userRight = $(this).attr('userid');
			}
			$('.selected img.user-gravatar', col).attr('src', $(this).attr('src')).css('visibility', 'visible');
			update();
		});
	});

	updateDistSpan(distMin, distMax);
	update();
});

function update(target_userid, taskid) {
	data = {'sprint': sprintid};

	if(target_userid != undefined && taskid != undefined) {
		data['targetUser'] = target_userid;
		data['task'] = taskid;
	}

	$.ajax({
		url: '/tasks/distribute/update',
		type: 'POST',
		data: data,
		success: function(data, text, request) {
			distData = data;
			console.log(distData);
			errorMessage = distData.error;
			process();
		},
		error: function(request, text, errorThrown) {
			distData = undefined;
			errorMessage = text + ' - ' + errorThrown;
			process();
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
		$('.distribution img.user-gravatar[userid=' + userid + ']').toggleClass('overcommitted', pcnt < distMin || pcnt > distMax);
	}

	['left', 'right'].forEach(function(side) {
		userid = (side == 'left') ? userLeft : userRight;
		user = distData[userid];
		info = $('.distribution.' + side + ' .info');
		tasks = $('.distribution.' + side + ' .tasks');
		if(user == undefined) {
			info.hide();
			tasks.empty();
		} else {
			pcnt = user.availability == 0 ? (user.hours > 0 ? 101 : 100) : Math.floor(user.hours * 100 / user.availability);
			$('.username', info).text(user.username);
			$('.hours', info).html(user.hours + ' / ' + user.availability + ' hours (' + user.tasks.length + (user.tasks.length == 1 ? ' task' : ' tasks') + ', ' + (user.availability == 0 && user.hours > 0 ? '&#8734;' : pcnt) + '%)');
			$('.task-progress-total .progress-current', info).css('width', Math.min(100, pcnt) + '%').css('visibility', pcnt > 0 ? 'visible' : 'hidden').toggleClass('progress-current-red', pcnt < distMin || pcnt > distMax);
			info.show();

			tasks.empty();
			for(i in user.groups) {
				group = user.groups[i];
				tasks.append($('<div/>').addClass('group').attr('groupid', group.id).text(group.name));
			}
			for(i in user.tasks) {
				task = user.tasks[i];
				row = $('<div/>').addClass('task').toggleClass('important', task.important).attr('taskid', task.id).text(task.text)
				$('.group[groupid=' + task.groupid + ']', tasks).append(row);
				row.click(function() {
					targetUser = (side == 'left' ? userRight : userLeft);
					if(targetUser != undefined) {
						update(targetUser, $(this).attr('taskid'));
					}
				});
			}
		}
	});
}
