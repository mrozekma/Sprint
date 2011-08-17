$(document).ready(function() {
	// TODO if grouping stays disabled, this can be pulled back out of a function
	fancy_cells('#all-tasks');

	setup_hours_events();
	setup_task_buttons();
	setup_filter_buttons();
	setup_group_arrows();

	$('#post-status').hide();
});

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
		val = parseInt(field.val(), 10);
		val += parseInt($(this).attr('amt'), 10);
		if(val < 0) {
			val = 0;
		}
		field.val('' + val)
		save_task(task, 'hours', val);
		set_status(task, val == 0 ? 'complete' : 'in progress');
	});

	$("td.hours input").blur(function(event) {
		task = $(this).parents('tr.task');
        field = $('input', $(this).parents('.hours'));
		val = parseInt(field.val(), 10);
		save_task(task, 'hours', val);
	});
}

/*
function setup_task_dragging() {
	$('table.tasks').sortable({'items': 'tr'});
	return;

	$('table.tasks').tableDnD({
		onDragStart: function(tbl, row) {
			row = $(row);
			if(row.hasClass('group')) { // Moving a group
				$('tr.task', $(tbl)).addClass('hide-temp');
			} else if(row.hasClass('task')) { // Moving a task
			}
		},

		onDrop: function(tbl, row) {
			row = $(row);
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
				new_group_id = row.prevAll('tr.group').attr('groupid');
				row.attr('groupid', new_group_id);

				pred = row.prev();
				if(pred.hasClass('task')) { // Inserted after a task
					// $('form').append($('<input>').attr('type', 'hidden').attr('name', 'taskmove').attr('value', row.attr('taskid') + ':' + pred.attr('taskid')));
					save_task(row, 'taskmove', pred.attr('taskid'));
				} else if(pred.hasClass('group')) { // Inserted after a group header (top of the group)
					//TODO Save
					unimplemented('Index 0 task move');
				} else {
					//FAIL
				}
			}
		}
	});
}

function setup_save_button() {
	$('#save-button').click(function() {
		// Fix new rows that are missing values
		$('tr.task[taskid="new"] td.name input')
			.filter(function() {
				return $(this).val() == '';
			})
			.val("Untitled Task");
		$('tr.task[taskid="new"] td.hours input')
			.filter(function() {
				return $(this).val() == '';
			})
			.val("1");

		$.post($('form').attr('action'), $('form').serialize(), function(data, text, request) {
			box = $('#post-status')
			switch(request.status) {
			case 200:
				box.attr('class', 'tint green');
				$('span', box).html(data);

				// $('.dirty').each(function() {
					// $(this).removeClass('dirty');
				// });
				break;
			case 298:
				box.attr('class', 'tint yellow');
				$('span', box).html(data);
				break;
			case 299:
				box.attr('class', 'tint red');
				$('span', box).html(data);
				break;
			default:
				box.attr('class', 'tint blood');
				$('span', box).html("Unexpected response code " + request.status)
				break;
			}

			box.fadeIn();
		});
	});
}
*/

function setup_task_buttons() {
	$('.actions img.task-new').click(function() {
		curRow = $(this).parents('tr.task');
		newRow = $("<tr class=\"task\" taskid=\"new\" groupid=\"" + curRow.attr('groupid') + "\" status=\"not started\" assigned=\"\">" +
				   "<td class=\"name\"><img src=\"/static/images/status-not-started.png\">&nbsp;<input type=\"text\" name=\"new_name\"></td>" +
				   "<td class=\"assigned\"><img src=\"/static/images/member.png\">&nbsp;<input type=\"text\" name=\"new_assigned\"></td>" +
				   "<td class=\"hours\">&nbsp;</td>" +
				   "<td class=\"hours\">&nbsp;</td>" +
				   "<td class=\"hours today\" nowrap><input type=\"text\" name=\"new_hours\"></td>" +
				   "<td class=\"actions\"><img src=\"/static/images/task-new.png\"></td>" +
				   "</tr>");
		curRow.after(newRow);
		$('input:first', newRow).focus();
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

// function dirty(cell) {
	// cell.parents('tr.task').addClass('dirty');
// }

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
}

function resort_tasks(sort) {
	var tasks, dateline, dateline2;

	// Find the existing task rows, and delete the tables holding them
	all = $('table#all-tasks');
	if(all.length > 0) { // first sort; pull every row from the master table
		tasks = $('tr.task', all);
		prnt = all.parent();
		dateline = $('tr.dateline', prnt);
		dateline2 = $('tr.dateline2', prnt);
		all.remove();
	} else { // resort; pull rows from existing sorted tables
		sorted = $('table.sorted-tasks');
		tasks = $('tr.task', sorted);
		prnt = sorted.parent();
		dateline = $('tr.dateline', prnt);
		dateline2 = $('tr.dateline2', prnt);
		sorted.remove();
	}

	// Create new tables and populate based on the sort type
	switch(sort) {
	case 'status':
		// statuses = ['blocked', 'canceled', 'complete', 'deferred', 'in progress', 'not started', 'split']; //TODO Dynamic
		statuses = ['complete', 'deferred'];
		for(i in statuses) {
			status = statuses[i];
			prnt.append($('<h1>' + status + '</h1>'));
			prnt.append($('<table>').addClass('tasks sorted-tasks').append(dateline).append(dateline2).append(tasks.filter('[status="' + status + '"]')));
		}
		fancy_cells('table.tasks.sorted-tasks');
		break;
	case 'owner':
		my_username = 'mmrozek'; //TODO Dynamic
		// There's probably an easier way to do this
		usernames = []
		tasks.each(function() {usernames.push($(this).attr('assigned'));});
		usernames.sort(function(a, b) {
			if(a == my_username) return -1;
			if(b == my_username) return 1;
			if(a < b) return -1;
			if(a > b) return 1;
			return 0;
		});

		last = '';
		for(i in usernames) {
			username = usernames[i];
			if(username == last) continue;
			last = username;

			prnt.append($('<h1>' + username + '</h1>'));
			prnt.append($('<table>').addClass('tasks sorted-tasks').append(dateline.clone()).append(dateline2.clone()).append(tasks.filter('[assigned="' + username + '"]')));
		}
		fancy_cells('table.tasks.sorted-tasks');
		break;
	default: //TODO
		alert('Invalid sort type: ' + sort);
		break;
	}
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
					save_task(row, 'taskmove', '[0]');
				} else if(pred.hasClass('task')) { // Inserted after a task
					save_task(row, 'taskmove', pred.attr('taskid'));
				} else if(pred.hasClass('group')) { // Inserted after a group header (top of the group)
					//TODO Save
					save_task(row, 'taskmove', '[' + new_group_id + ']');
				} else {
					//FAIL
				}
			}
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
				save_task(task, 'name', c.current);
			}
		}
	});

	$('td.assigned > span', $(table_selector)).editable({
		onSubmit: function(c) {
			id = $(this).attr('id').replace('assigned_span_', '');
			$('[name="assigned[' + id + ']"]').val(c.current);
			$('tr', $(this)).attr('assigned', c.current);
			$(this).attr('username', c.current);
			if(c.previous != c.current) {
				task = $(this).parents('tr.task');
				// dirty($(this));
				save_task(task, 'assigned', c.current);
			}
		}
	});

	$('tr.task img.status').contextMenu({
		menu: 'status-menu'
	}, function(action, el, pos) {
		task = $(el).parents('tr.task');
		set_status(task, action);
	});

	$('tr.task img.goal').contextMenu({
		menu: 'goal-menu'
	}, function(action, el, pos) {
		task = $(el).parents('tr.task');
		id = $(el).attr('id').replace('goal_', '');
		field = $('[name="goal[' + id + ']"]');
		console.log(action);
		console.log(id);
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
	}
}

function save_task(task, field, value) {
	save_fields(task.attr('taskid'), task.attr('revid'), field, value);
}

function save_fields(task_id, old_rev_id, field, value) {
	//TODO
	console.log("Saving change to " + task_id + "(" + old_rev_id + "): " + field + " <- " + value);
	$.post("/sprints/" + sprintid + "/post", {'id': task_id, 'rev_id': old_rev_id, 'field': field, 'value': value}, function(data, text, request) {
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
			$('tr.task[taskid=' + task_id + ']').attr('revid', data);
			console.log("Changed saved; new revision is " + data);
			return;
		default:
			box.attr('class', 'tint blood');
			$('span', box).html("Unexpected response code " + request.status)
			break;
		}

		box.fadeIn();
	});
}

function delete_task(task_id) {
	row = $('tr.task[taskid=' + task_id + ']');
	if(row) {
		row.fadeOut();
		//TODO Post
	}
}

function unimplemented(what) {
	box = $('#post-status');
	box.attr('class', 'tint yellow');
	$('span', box).html("<b>Unimplemented</b>: " + what);
	box.fadeIn();
}