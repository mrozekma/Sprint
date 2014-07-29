$(document).ready(function() {
	setup_search();
	setup_filter_buttons();
	setup_indexes();
	setup_warnings();
	$('#post-status').hide();
});

function setup_search() {
	$('input#search').keydown(function(e) {
		if(e.keyCode == 13) {
			document.location = '/sprints/' + sprintid + '?search=' + encodeURIComponent($(this).val());
		}
	});
}

function setup_filter_buttons() {
	$.each(['#filter-assigned', '#filter-status'], function(_, selector) {
		$(selector + ' a:gt(0)').click(function(e) {
			if(e.ctrlKey) {
				$(this).toggleClass('selected');
			} else {
				$(selector + ' a').removeClass('selected');
				$(this).addClass('selected');
			}

			apply_filters();
			return false;
		});

		$(selector + ' a:first').click(function(e) {
			$(selector + ' a').removeClass('selected');
			apply_filters();
			return false;
		});
	});
}

function setup_indexes() {
	$('tr.task .task-index').click(function(e) {
		task = $(this).parents('tr.task');
		task.toggleClass('selected');

		if(e.shiftKey) {
			$('tr.task:visible').toggleClass('selected', task.hasClass('selected'));
		} else if(e.ctrlKey) {
			group_id = task.attr('groupid');
			group_tasks = $('tr.task[groupid=' + group_id + ']:visible');
			group_tasks.toggleClass('selected', task.hasClass('selected'));
		}

		selected = $('tr.task.selected');
		box = $('#selected-task-box');
		if(selected.length > 0) {
			$('span', box).text(selected.length + (selected.length == 1 ? ' task' : ' tasks') + ' selected');
			box.slideDown('fast');
		} else {
			box.slideUp('fast');
		}
	});

	$('#selected-task-box #selected-history').click(function(e) {
		ids = $('tr.task.selected').map(function() {return $(this).attr('taskid');});
		idStr = $.makeArray(ids).join();
		if(e.button == 1 || e.ctrlKey) {
			window.open('/tasks/' + idStr);
		} else {
			document.location = '/tasks/' + idStr;
		}
		$('#selected-task-box #selected-cancel').click();
		e.preventDefault();
	});

	$('#selected-task-box #selected-highlight').click(function(e) {
		ids = $('tr.task.selected').map(function() {return $(this).attr('taskid');});
		idStr = $.makeArray(ids).join();
		if(e.button == 1 || e.ctrlKey) {
			window.open('?search=highlight:' + idStr);
		} else {
			document.location.search = 'search=highlight:' + idStr;
		}
		$('#selected-task-box #selected-cancel').click();
		e.preventDefault();
	});

	$('#selected-task-box #selected-edit').click(function(e) {
		ids = $('tr.task.selected').map(function() {return $(this).attr('taskid');});
		idStr = $.makeArray(ids).join();
		if(e.button == 1 || e.ctrlKey) {
			window.open('/tasks/' + idStr + '/edit');
		} else {
			document.location = '/tasks/' + idStr + '/edit';
		}
		$('#selected-task-box #selected-cancel').click();
		e.preventDefault();
	});

	$('#selected-task-box #selected-cancel').click(function() {
		$('tr.task.selected .task-index').click();
	});

	update_indexes();
}

function setup_warnings() {
	$('#sprint-warnings .header').click(function() {
		box = $('#sprint-warnings');
		box.toggleClass('expanded');
		if(box.hasClass('expanded')) {
			$('.header img', box).attr('src', '/static/images/collapse.png');
			$('ul', box).show();
		} else {
			$('.header img', box).attr('src', '/static/images/expand.png');
			$('ul', box).hide();
		}
	});
}

function tasktable_visibility_hook() {
	apply_filters();
}

function apply_filters() {
	assigned = $('#filter-assigned a.selected');
	statuses = $('#filter-status a.selected');
	groups = $('tr.group');
	tasks = $('tr.task');

	groups.show();
	tasks.show();

	if(assigned.length > 0) {
		$('#filter-assigned a:not(.selected)').each(function() {
			tasks.filter('[assigned="' + $(this).attr('assigned') + '"]').hide();
		});

		// Special-case many-assigned tasks; hide if all of the assignees are unselected
		tasks.filter('[assigned*=" "]').each(function() {
			task_assigned = $(this).attr('assigned').split(' ');
			for(i in task_assigned) {
				if($('#filter-assigned a[assigned=' + task_assigned[i] + ']').hasClass('selected')) {
					return;
				}
			}
			$(this).hide();
		});
	}

	if(statuses.length > 0) {
		$('#filter-status a:not(.selected)').each(function() {
			tasks.filter('[status="' + $(this).attr('status') + '"]').hide();
		});
	}

	$('tr.group img[src="/static/images/expand.png"]').each(function(e) {
		groupid=$(this).parents('tr').attr('groupid');
		$('tr.task[groupid=' + groupid + ']').hide();
	});

	if(assigned.length > 0 || statuses.length > 0) {
		// Hide non-fixed groups with no tasks
		groups.each(function() {
			seek = $(this);
			if(seek.hasClass('fixed')) {
				return;
			}
			while(seek = seek.next()) {
				if(seek.is('.task:visible')) {
					return;
				} else if(seek.length == 0 || seek.hasClass('group')) {
					$(this).hide();
					return;
				}
			}
		});
	}

	// Set the new task assignee parameters
	qs_assigned = $.makeArray(assigned.map(function() {return $(this).attr('assigned');})).join(' ');
	$('a[href^="/tasks/new"]').each(function() {
		qs = $.deparam.querystring($(this).attr('href'));
		qs['assigned'] = qs_assigned;
		$(this).attr('href', $.param.querystring('/tasks/new', qs));
		return;
	});

	update_task_count();
	update_indexes();
}

function save_error(text, fatal) {
	if(fatal === undefined) {fatal = true;}
	noty({type: fatal ? 'error' : 'warning', text: text})
}

savingMutex = false;
function tasktable_change_hook(task, field, value, counter) {
	console.log("Saving change to " + task.attr('taskid') + "(" + task.attr('revid') + "): " + field + " <- " + value + " (attempt " + (counter == undefined ? 0 : counter) + ")");
	$('.saving', task).css('visibility', 'visible');

	if(savingMutex) {
		if(counter == 10) {
			save_error("Timed out trying to set task " + task.attr('taskid') + " " + field + " to " + value);
			$('.saving', task).css('visibility', 'hidden');
		} else {
			setTimeout(function() {tasktable_change_hook(task, field, value, (counter == undefined ? 0 : counter) + 1);}, 200);
		}
		return;
	}

	savingMutex = true;
	$.post("/sprints/" + sprintid, {'id': task.attr('taskid'), 'rev_id': task.attr('revid'), 'field': field, 'value': value}, function(data, text, request) {
		switch(request.status) {
		case 200:
			save_error(data)
			break;
		case 298:
			save_error(data, false);
			break;
		case 299:
			rev = parseInt(data, 10);
			$('tr.task[taskid=' + task.attr('taskid') + ']').attr('revid', rev).addClass('changed-today');
			console.log("Changed saved; new revision is " + rev);
			break;
		default:
			save_error("Unexpected response code " + request.status)
			break;
		}

		$('.saving', task).css('visibility', 'hidden');
		savingMutex = false;
	});
}
