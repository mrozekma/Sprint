$(document).ready(function() {
	// TODO if grouping stays disabled, this can be pulled back out of a function
	fancy_cells('#all-tasks');

	setupHoursEvents();
	setupTaskDragging();
	setupSaveButton();
	setupTaskButtons();
	setupFilterButtons();
	setupGroupArrows();

	$('#post-status').hide();
});

function setupHoursEvents() {
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
        field = $('input', $(this).parents('.hours'));
		val = parseInt(field.val(), 10);
		val += parseInt($(this).attr('amt'), 10);
		if(val < 0)
			val = 0;
		field.val('' + val)
		dirty($(this));
	});

	$("td.hours input").keydown(function(event) {
		dirty($(this));
	});
}

function setupTaskDragging() {
	$('table.tasks').tableDnD({
		onDragStart: function(tbl, row) {
			if($(row).hasClass('group')) { // Moving a group
				$('tr.task', $(tbl)).addClass('hide-temp');
			} else if($(row).hasClass('task')) { // Moving a task
			}
		},

		onDrop: function(tbl, row) {
			row = $(row);
			$('tr.task.hide-temp').removeClass('hide-temp');
			row.addClass('dirty');
			if(row.hasClass('group')) {
				$('tr.group').each(function() {
					groupid = $(this).attr('groupid');
					$('tr.task[groupid=' + groupid + ']').insertAfter($(this));
				});
			} else if(row.hasClass('task')) {
				newGroupID = row.prevAll('tr.group').attr('groupid');
				row.attr('groupid', newGroupID);

				pred = row.prev();
				if(pred.hasClass('task')) { // Inserted after a task
					$('form').append($('<input>').attr('type', 'hidden').attr('name', 'taskmove').attr('value', row.attr('taskid') + ':' + pred.attr('taskid')));
				} else if(pred.hasClass('group')) { // Inserted after a group header (top of the group)
					$('form').append($('<input>').attr('type', 'hidden').attr('name', 'taskmove').attr('value', row.attr('taskid') + ':[' + pred.attr('groupid') + ']'));
				} else {
					//FAIL
				}
			}
		}
	});
}

function setupSaveButton() {
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

				$('.dirty').each(function() {
					$(this).removeClass('dirty');
				});
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

function setupTaskButtons() {
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

function setupFilterButtons() {
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

function setupGroupArrows() {
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
			break;
		}
	});
}

function dirty(cell) {
	cell.parents('tr.task').addClass('dirty');
}

function apply_filters() {
	assigned = $('#filter-assigned a.selected');
	status = $('#filter-status a.selected');
	tasks = $('tr.task');

	tasks.show();

	if(assigned.length > 0) {
		$('#filter-assigned a:not(.selected)').each(function() {
			tasks.filter('[assigned="' + $(this).attr('assigned') + '"]').hide();
		});
	}

	if(status.length > 0) {
		$('#filter-status a:not(.selected)').each(function() {
			tasks.filter('[status="' + $(this).attr('status') + '"]').hide();
		});
	}
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
	$(table_selector).tableDnD({onDragClass: 'dragging'});
	// return;
	$('td.name > span', $(table_selector)).editable({
		onSubmit: function(c) {
			id = $(this).attr('id').replace('name_span_', '');
			$('[name="name[' + id + ']"]').val(c.current);
			if(c.previous != c.current)
				dirty($(this));
		}
	});

	$('td.assigned > span', $(table_selector)).editable({
		onSubmit: function(c) {
			id = $(this).attr('id').replace('assigned_span_', '');
			$('[name="assigned[' + id + ']"]').val(c.current);
			$('tr', $(this)).attr('assigned', c.current);
			$(this).attr('username', c.current);
			if(c.previous != c.current)
				dirty($(this));
		}
	});

	$('td.name img').contextMenu({
		menu: 'status-menu'
	}, function(action, el, pos) {
		id = $(el).attr('id').replace('status_', '');
		field = $('[name="status[' + id + ']"]');
		if(field.val() != action) {
			$(el).parents('tr').attr('status', action);
			field.val(action);
			$(el).attr('src', '/static/images/status-' + action.replace(' ', '-') + '.png');
			dirty($(el));
		}

		/*
		alert(
			'Action: ' + action + '\n\n' +
				'Element ID: ' + $(el).attr('id') + '\n\n' + 
				'X: ' + pos.x + '  Y: ' + pos.y + ' (relative to element)\n\n' + 
				'X: ' + pos.docX + '  Y: ' + pos.docY+ ' (relative to document)'
		);
		*/
	});
}
