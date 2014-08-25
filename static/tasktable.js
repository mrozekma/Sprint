$(document).ready(function() {
	tasktable_init();
});

function tasktable_init() {
	fancy_cells('.tasktable.editable');

	setup_hours_events();
	setup_group_arrows();
	setup_checkboxes();

	$('.saving').css('visibility', 'hidden');
}

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
		hours_blur($(this), true);
	}).keypress(function(event) {
		field = $(this);
		clearTimeout(hours_timer);
		hours_timer = setTimeout(function() {
			hours_timer = null;
			hours_blur(field, false);
		}, 750);
	});
}

function hours_blur(field, done) {
	clearTimeout(hours_timer);
	task = field.parents('tr.task');
	field = $('input', field.parents('.hours'));
	val = parseInt(field.val(), 10);
	if(hours_cache < 0) {
		console.log("Problem blurring hours field; hours cache is unset");
	} else if(isNaN(val)) {
		if(done) {
			field.val(hours_cache);
		}
	} else if(val != hours_cache) {
		hours_cache = val;
		save_task(task, 'hours', val);
		if(!isPlanning) {
			set_status(task, val == 0 ? 'complete' : 'in progress');
		}
	}
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
			if(typeof(tasktable_visibility_hook) == 'function') {
				tasktable_visibility_hook();
			}
			break;
		}
	});
}

function setup_checkboxes() {
	// When the group checkbox is clicked, toggle all task checkboxes in the group
	$('tr.group input[type="checkbox"]').change(function(e) {
		group = $(this).parents('tr.group');
		groupid = group.attr('groupid');
		$('tr.task[groupid="' + groupid + '"] input[type="checkbox"]').prop('checked', $(this).prop('checked'));
	});

	// When a task checkbox is clicked, possibly update the group checkbox state
	$('tr.task input[type="checkbox"]').change(function(e) {
		task = $(this).parents('tr.task');
		groupid = task.attr('groupid');
		groupbox = $('tr.group[groupid="' + groupid + '"] input[type="checkbox"]');
		taskboxes = $('tr.task[groupid="' + groupid + '"] input[type="checkbox"]');

		groupbox.prop('checked', (taskboxes.not(':checked').length == 0));
	});
}

function update_indexes() {
	i = 0;
	$('.task:visible .task-index').each(function() {
		$(this).text(++i);
	});
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
			if(row.hasClass('group')) {
				// Move all the group's tasks under the group header row
				$('tr.group').each(function() {
					groupid = $(this).attr('groupid');
					$('tr.task[groupid=' + groupid + ']').insertAfter($(this));
				});

				new_seq = row.prevUntil('table', 'tr.group').length + 1;
				save_rev(row.attr('groupid'), 'groupmove', new_seq);
			} else if(row.hasClass('task')) {
				new_group = row.prevAll('tr.group');
				if(new_group.length == 0) { // Dragged above the first group
					console.log('Bad drag target');
					$(this).sortable('cancel');
					return;
				}
				new_group_id = new_group.attr('groupid');
				new_seq = row.prevUntil('tr.group', 'tr.task').length + 1;
				row.attr('groupid', new_group_id);
				save_task(row, 'taskmove', new_group_id + ':' + new_seq);
			}
			update_indexes();
		},
	});

	editFn = function() {
		oldValue = $(this).text();
		field = $('<input>').attr('type', 'text').attr('id', $(this).attr('id')).val(oldValue);
		$(this).replaceWith(field);
		field.select();
		uneditFn = function(text) {
				if($(this).val() != oldValue) {
					save_task($(this).parents('tr.task'), 'name', $(this).val());
				}

				span = $('<span>').text(text);
				$(this).replaceWith(span);
				span.click(editFn);
		};

		field.keyup(function(e) {
			switch(e.keyCode) {
			case 13:
				uneditFn.call(this, $(this).val());
				break;
			case 27:
				uneditFn.call(this, oldValue);
				break;
			}
		});

		field.blur(function() {
			uneditFn.call(this, $(this).val());
		});
	};

	$('td.name > span', $(table_selector)).click(editFn);

	$('td.assigned > span', $(table_selector)).contextMenu({
		menu: 'assigned-menu',
		preShow: function(menu, el) {
			// Mark the right users as already assigned
			$('li.selected', menu).removeClass('selected');
			assigned = $(el).parents('tr.task').attr('assigned').split(' ');
			for(i in assigned) {
				$('li a[href="#' + assigned[i] + '"]', menu).parents('li').addClass('selected');
			}

			// Find list of current teams
			teams = {}
			$('[assigned*=" "]', $(table_selector)).each(function() {
				teams[$(this).attr('assigned')] = 1;
			});

			// Add links for current teams
			$('li.team', menu).remove();
			for(team in teams) {
				if(team == assigned.join(' ')) {
					continue;
				}

				node = $('<li/>');
				node.addClass('team separator');
				node.append($('<a href="#' + team + '"/>').text(team));
				menu.append(node);
			}
		}
	}, function(action, el, pos, e) {
		task = $(el).parents('tr.task');

		if(action.indexOf(' ') >= 0) {
			assigned = action.split(' ');
		} else if(e.ctrlKey) {
			assigned = task.attr('assigned').split(' ');
			idx = assigned.indexOf(action);
			if(idx >= 0) {
				if(assigned.length == 1) {
					return;
				}
				assigned.splice(idx, 1);
			} else {
				assigned.push(action);
			}
		} else {
			assigned = [action];
		}

		assigned.sort();
		assigned_str = assigned.join(' ');
		if(task.attr('assigned') == assigned_str) {
			return;
		}

		task.attr('assigned', assigned_str);
		if(assigned.length > 1) {
			$('td.assigned span img', task).attr('src', '/static/images/team.png');
			$('td.assigned span span.username', task)
				.attr('username', assigned_str)
				.attr('title', assigned_str)
				.text("team (" + assigned.length + ")");
		} else {
			$('td.assigned span img', task).attr('src', '/static/images/member.png');
			$('td.assigned span span.username', task)
				.attr('username', assigned[0])
				.attr('title', '')
				.text(assigned[0]);
		}

		save_task(task, 'assigned', assigned_str);
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
		if(['canceled', 'split', 'complete'].indexOf(status_name) >= 0) {
			$('td.hours input', task).val('0');
			save_task(task, 'hours', 0);
		}
	}
}

function delete_task(task_id) {
	row = $('tr.task[taskid=' + task_id + ']');
	if(row) {
		save_task(row, 'deleted', true);
		if(row.hasClass('selected')) {
			$('.task-index', row).click();
		}
		row.fadeOut();
		row.hide();
		totalTasks--;
		if(tasktable_visibility_hook !== undefined) {
			tasktable_visibility_hook();
		}
		update_indexes();
	}
}

function unimplemented(what) {
	noty({type: 'error', text: '<b>Unimplemented</b>: ' + what})
}

function save_task(task, field, value) {
	save_rev(task.attr('taskid'), field, value);
}

function save_rev(id, field, value) {
	if(typeof(tasktable_change_hook) == 'function') {
		tasktable_change_hook(id, field, value, 0);
	}
}
