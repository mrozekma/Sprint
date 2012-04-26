$(document).ready(function() {
	// TODO if grouping stays disabled, this can be pulled back out of a function
	fancy_cells('#all-tasks.editable');

	setup_hours_events();
	setup_search();
	setup_filter_buttons();
	setup_group_arrows();
	setup_bugzilla($('tr.task'));
	setup_indexes();

	$('#post-status').hide();
	$('.saving').css('visibility', 'hidden');
});

hours_cache = -1;
hours_timer = null;
function setup_hours_events() {
	$('td.hours img').css('opacity', 0);

	$('td.hours').hover(
		function() {
			// $('img', this).fadeIn();
			$('img', this).animate({opacity: 1});
		},
		function() {
			// $('img', this).fadeOut();
			$('img', this).animate({opacity: 0});
		}
	);

	$('td.hours img').hover(
		function() {
			$(this).attr('src', $(this).attr('src').match(/[^\.]+/) + '-lit.png');
		},
		function() {
			$(this).attr('src', $(this).attr('src').replace('-lit', ''));
		}
	);

	$('td.hours img').click(function() {
		task = $(this).parents('tr.task');
		field = $('input', $(this).parents('.hours'));
		old_val = val = parseInt(field.val(), 10);
		val += parseInt($(this).attr('amt'), 10);
		if(val < 0) {
			if(old_val == 0) {
				return;
			} else {
				val = 0;
			}
		}
		field.val('' + val)
		save_task(task, 'hours', val);
		if(!isPlanning) {
			set_status(task, val == 0 ? 'complete' : 'in progress');
		}
	});

	$("td.hours input").focus(function(event) {
		hours_cache = parseInt($('input', $(this).parents('.hours')).val(), 10);
	}).blur(function(event) {
		hours_blur($(this));
	}).keypress(function(event) {
		field = $(this);
		clearTimeout(hours_timer);
		hours_timer = setTimeout(function() {
			hours_timer = null;
			hours_blur(field);
		}, 750);
	});
}

function hours_blur(field) {
	clearTimeout(hours_timer);
	task = field.parents('tr.task');
	field = $('input', field.parents('.hours'));
	val = parseInt(field.val(), 10);
	if(hours_cache < 0) {
		console.log("Problem blurring hours field; hours cache is unset");
	} else if(val != hours_cache) {
		save_task(task, 'hours', val);
		if(!isPlanning) {
			set_status(task, val == 0 ? 'complete' : 'in progress');
		}
	}
}

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

function setup_group_arrows() {
	$('tr.group img').click(function(e) {
		switch($(this).attr('src')) {
		case '/static/images/collapse.png':
			$(this).attr('src', '/static/images/expand.png');
			groupid=$(this).parents('tr').attr('groupid');
			$('tr.task[groupid=' + groupid + ']').hide();
			break;
		case '/static/images/expand.png':
			$(this).attr('src', '/static/images/collapse.png');
			groupid=$(this).parents('tr').attr('groupid');
			$('tr.task[groupid=' + groupid + ']').show();
			apply_filters();
			break;
		}
	});
}

function setup_bugzilla(tasks) {
	tasks.each(function() {
		name = $('td.name span', $(this)).text();
		link = $('td.actions a.bugzilla', $(this));

		//TODO Support multiple bugs in one task
		/*
		re = /(?:bug |bz)([0-9]+)/gi;
		while(match = re.exec(name)) {
			id = parseInt(match[1], 10);
		}
		*/

		if(match = name.match(/(?:bug |bz)([0-9]+)/i)) {
			id = parseInt(match[1], 10);
			link.attr('href', 'http://bugs.arxandefense.com/show_bug.cgi?id=' + id);
			link.show();
		} else {
			link.hide();
		}
	});
}

function setup_indexes() {
	$('tr.task .task-index').click(function() {
		task = $(this).parents('tr.task');
		task.toggleClass('selected');

		selected = $('tr.task.selected');
		box = $('#selected-task-box');
		if(selected.length > 0) {
			$('span', box).text(selected.length + (selected.length == 1 ? ' task' : ' tasks') + ' selected');
			box.slideDown('fast');
		} else {
			box.slideUp('fast');
		}
	});

	$('#selected-task-box #selected-history').click(function() {
		ids = $('tr.task.selected').map(function() {return $(this).attr('taskid');});
		idStr = $.makeArray(ids).join();
		document.location = '/tasks/' + idStr;
	});

	$('#selected-task-box #selected-highlight').click(function() {
		ids = $('tr.task.selected').map(function() {return $(this).attr('taskid');});
		idStr = $.makeArray(ids).join();
		document.location.search = 'search=highlight:' + idStr;
	});

	$('#selected-task-box #selected-cancel').click(function() {
		$('tr.task.selected .task-index').click();
	});

	update_indexes();
}

function update_indexes() {
	i = 0;
	$('.task:visible .task-index').each(function() {
		$(this).text(++i);
	});
}

function apply_filters() {
	assigned = $('#filter-assigned a.selected');
	statuses = $('#filter-status a.selected');
	tasks = $('tr.task');

	tasks.show();

	if(assigned.length > 0) {
		$('#filter-assigned a:not(.selected)').each(function() {
			tasks.filter('[assigned="' + $(this).attr('assigned') + '"]').hide();
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

	update_task_count();
	update_indexes();
}

function fancy_cells(table_selector) {
	$(table_selector).sortable({
		items: 'tr:not(.nodrag)',
		containment: table_selector,
		start: function(event, ui) {
			row = $(ui.item[0]);
			if(row.hasClass('group')) { // Moving a group
				$('tr.task', $(table_selector)).addClass('hide-temp');
			} else if(row.hasClass('task')) { // Moving a task
			}
		},
		stop: function(event, ui) {
			row = $(ui.item[0]);
			$('tr.task.hide-temp').removeClass('hide-temp');
			// row.addClass('dirty');
			if(row.hasClass('group')) {
				// Move all the group's tasks under the group header row
				$('tr.group').each(function() {
					groupid = $(this).attr('groupid');
					$('tr.task[groupid=' + groupid + ']').insertAfter($(this));
				});

				//TODO Save new group position
				unimplemented('Group move');
			} else if(row.hasClass('task')) {
				new_group = row.prevAll('tr.group');
				new_group_id = new_group.length ? new_group.attr('groupid') : 0;
				row.attr('groupid', new_group_id);

				pred = row.prev();
				if(!pred.length) { // First row in the table
					save_task(row, 'taskmove', ':0');
				} else if(pred.hasClass('task')) { // Inserted after a task
					save_task(row, 'taskmove', pred.attr('taskid'));
				} else if(pred.hasClass('group')) { // Inserted after a group header (top of the group)
					//TODO Save
					save_task(row, 'taskmove', ':' + new_group_id);
				} else {
					//FAIL
				}
			}
			update_indexes();
		},
	});

	// $(table_selector).tableDnD({onDragClass: 'dragging'});
	// return;
	$('td.name > span', $(table_selector)).editable({
		onSubmit: function(c) {
			id = $(this).attr('id').replace('name_span_', '');
			$('[name="name[' + id + ']"]').val(c.current);
			if(c.previous != c.current) {
				task = $(this).parents('tr.task');
				// dirty($(this));
				setup_bugzilla(task);
				save_task(task, 'name', c.current);
			}
		}
	});

	$('td.assigned > span', $(table_selector)).click(function() {
		task = $(this).parents('tr.task');
		sel = $('<select/>');
		for(i in usernames) {
			opt = $("<option>").text(usernames[i]).attr('selected', usernames[i] == task.attr('assigned'));
			sel.append(opt);
		}
		$(this).replaceWith(sel);
		// sel.chosen();
		sel.change(function() {
			task.attr('assigned', $(this).val());
			save_task(task, 'assigned', $(this).val());
		});
	});

	$('tr.task img.status', $(table_selector)).contextMenu({
		menu: 'status-menu'
	}, function(action, el, pos) {
		task = $(el).parents('tr.task');
		set_status(task, action);
	});

	$('tr.task img.goal', $(table_selector)).contextMenu({
		menu: 'goal-menu'
	}, function(action, el, pos) {
		task = $(el).parents('tr.task');
		id = $(el).attr('id').replace('goal_', '');
		field = $('[name="goal[' + id + ']"]');
		if(field.val() != action) {
			task.attr('goal', action);
			field.val(action);
			$(el).attr('src', goal_imgs[action]);
			$(el).attr('title', goal_texts[action]);
			save_task(task, 'goal', action);
		}
	});
}

function set_status(task, status_name) {
	node = $('img.status', task);
	id = node.attr('id').replace('status_', '');
	field = $('[name="status[' + id + ']"]');
	if(field.val() != status_name) {
		task.attr('status', status_name);
		field.val(status_name);
		node.attr('src', '/static/images/status-' + status_name.replace(' ', '-') + '.png');
		node.attr('title', status_texts[status_name]);
		save_task(task, 'status', status_name);
		if(['canceled', 'deferred', 'split'].indexOf(status_name) >= 0) {
			$('td.hours input', task).val('0');
			save_task(task, 'hours', 0);
		}
	}
}

savingMutex = false;
function save_task(task, field, value, counter) {
	console.log("Saving change to " + task.attr('taskid') + "(" + task.attr('revid') + "): " + field + " <- " + value + " (attempt " + (counter == undefined ? 0 : counter) + ")");
	$('.saving', task).css('visibility', 'visible');

	if(savingMutex) {
		if(counter == 10) {
			box = $('#post-status');
			box.attr('class', 'alert-message error');
			$('span.boxbody', box).html("Timed out trying to set task " + task.attr('taskid') + " " + field + " to " + value);
			showbox(box);
			$('.saving', task).css('visibility', 'hidden');
		} else {
			setTimeout(function() {save_task(task, field, value, (counter == undefined ? 0 : counter) + 1);}, 200);
		}
		return;
	}

	savingMutex = true;
	$.post("/sprints/" + sprintid, {'id': task.attr('taskid'), 'rev_id': task.attr('revid'), 'field': field, 'value': value}, function(data, text, request) {
		box = $('#post-status')
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
			$('tr.task[taskid=' + task.attr('taskid') + ']').attr('revid', data);
			console.log("Changed saved; new revision is " + data);
			box.fadeOut();
			box = null;
			break;
		default:
			box.attr('class', 'alert-message success');
			$('span.boxbody', box).html("Unexpected response code " + request.status)
			break;
		}

		if(box) {
			showbox(box);
		}
		$('.saving', task).css('visibility', 'hidden');
		savingMutex = false;
	});
}

function delete_task(task_id) {
	row = $('tr.task[taskid=' + task_id + ']');
	if(row) {
		save_task(row, 'deleted', 1);
		row.fadeOut();
		row.hide();
		totalTasks--;
		update_task_count();
		update_indexes();
	}
}

function unimplemented(what) {
	box = $('#post-status');
	box.attr('class', 'alert-message warning');
	$('span.boxbody', box).html("<b>Unimplemented</b>: " + what);
	showbox(box);
}