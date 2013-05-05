var distMin = 40, distMax = 80;
var distData = undefined;
var errorMessage = undefined;
var userLeft = undefined, userRight = undefined;
var chart = undefined;

$(document).ready(function() {
	updateSuccess = function(data, text, request) {
		distData = data;
		errorMessage = distData.error;
		process();
	}

	updateFail = function(data, text, errorThrown) {
		distData = undefined;
		errorMessage = text + ' - ' + errorThrown;
		process();
	}

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
		req = update();
		$(this).effect('transfer', {
			to: '.distribution.' + side + ' .selected img.user-gravatar',
			className: 'distribution-transfer'
		}, 'fast', function() {
			if(side == 'left') {
				userLeft = null;
				process();
				userLeft = $(this).attr('userid');
			} else {
				userRight = null;
				process();
				userRight = $(this).attr('userid');
			}
			$('.selected img.user-gravatar', col).attr('src', $(this).attr('src')).css('visibility', 'visible');
			req.done(updateSuccess).fail(updateFail);
		});
	});

	updateDistSpan(distMin, distMax);
	update().done(updateSuccess).fail(updateFail);
});

function update(target_userid, taskid) {
	data = {'sprint': sprintid};

	if(target_userid != undefined && taskid != undefined) {
		data['targetUser'] = target_userid;
		data['task'] = taskid;
	}

	return $.ajax({
		url: '/tasks/distribute/update',
		type: 'POST',
		data: data
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

	['left', 'right'].forEach(function(side) {
		userid = (side == 'left') ? userLeft : userRight;
		user = distData[userid];
		info = $('.distribution.' + side + ' .info');
		tasks = $('.distribution.' + side + ' .tasks');
		if(userid == 'deferred') {
			$('.username', info).text('Deferred tasks');
			$('.hours', info).html('&nbsp;');
			$('.task-progress-total', info).hide();
			info.show();
			tasks.addClass('deferred');

			tasks.empty();
			for(i in user.groups) {
				group = user.groups[i];
				tasks.append($('<div/>').addClass('group').attr('groupid', group.id).text(group.name));
			}
			for(i in user.tasks) {
				task = user.tasks[i];
				row = $('<div/>').addClass('task').attr('taskid', task.id).text(task.name)
				$('.group[groupid=' + task.groupid + ']', tasks).append(row);
			}
		} else if(user == undefined) {
			$('.username', info).text('Loading...');
			$('.hours', info).html('&nbsp;');
			$('.task-progress-total .progress-current', info).css('visibility', 'hidden');
			tasks.empty();
			tasks.removeClass('deferred');
		} else {
			pcnt = user.availability == 0 ? (user.hours > 0 ? 101 : 100) : Math.floor(user.hours * 100 / user.availability);
			$('.username', info).text(user.username);
			$('.hours', info).html(user.hours + ' / ' + user.availability + ' hours (' + user.tasks.length + (user.tasks.length == 1 ? ' task' : ' tasks') + ', ' + (user.availability == 0 && user.hours > 0 ? '&#8734;' : pcnt) + '%)');
			$('.task-progress-total .progress-current', info).css('width', Math.min(100, pcnt) + '%').css('visibility', pcnt > 0 ? 'visible' : 'hidden').toggleClass('progress-current-red', pcnt < distMin || pcnt > distMax);
			$('.task-progress-total', info).show();
			info.show();

			tasks.empty();
			for(i in user.groups) {
				group = user.groups[i];
				tasks.append($('<div/>').addClass('group').attr('groupid', group.id).text(group.name));
			}
			for(i in user.tasks) {
				task = user.tasks[i];
				row = $('<div/>').addClass('task').toggleClass('important', task.important).toggleClass('team', task.team).attr('taskid', task.id).text('(' + task.hours + ') ' + task.name)
				$('.group[groupid=' + task.groupid + ']', tasks).append(row);
				row.click(function() {
					targetUser = (side == 'left' ? userRight : userLeft);
					if(targetUser != undefined) {
						update(targetUser, $(this).attr('taskid')).done(updateSuccess).fail(updateFail);
					}
				});
			}
		}
	});

	showChart();
}

function showChart() {
	categories = []
	data = []
	usernames = []
	nameToID = {}
	for(userid in distData) {
		if(userid == 'deferred') {continue;}
		user = distData[userid];
		usernames.push(user.username);
		nameToID[user.username] = userid;
	}
	usernames.sort();
	for(i in usernames) {
		userid = nameToID[usernames[i]];
		user = distData[userid];
		pcnt = user.availability == 0 ? 100 : Math.min(Math.floor(user.hours * 100 / user.availability), 100);

		categories.push(user.username);
		data.push({
			y: pcnt,
			color: (pcnt < distMin) ? '#4572A7' : (pcnt > distMax) ? '#AA4643' : '#4BB24D'
		});
	}

	if(chart == undefined) {
		chart = new Highcharts.Chart({
			chart: {
				renderTo: 'distribution-chart',
				animation: false,
				polar: true
			},

			title: {
				text: ''
			},

			credits: {
				enabled: false
			},

			legend: {
				enabled: false
			},

			tooltip: {
				enabled: false
			},

			xAxis: {
				categories: categories
			},

			yAxis: {
				min: 0,
				max: 100,
				tickInterval: 50,
				minorTickInterval: 10,
				labels: {
					enabled: false
				}
			},

			series: [{
				type: 'column',
				name: 'Column',
				data: data
			}]
		});
	} else {
		chart.series[0].setData(data);
	}
}
