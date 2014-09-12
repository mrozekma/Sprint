TaskTable = (function() {
	event_anchor = {};
	hours_cache = -1;
	hours_timer = null;
	link_hours_status = null; // mark tasks complete at 0 hours, and vice versa

	function init(opts) {
		$(document).ready(function() {
			opts = opts || {};
			link_hours_status = opts['link_hours_status'] || false;

			fancy_cells('.tasktable.editable');
			setup_hours_events();
			setup_group_arrows();
			setup_checkboxes();

			$('.saving').css('visibility', 'hidden');
		});
	}

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
			field = $('.hours input', task);
			old_val = val = parseInt(field.val(), 10);
			val += parseInt($(this).attr('amt'), 10);
			if(val < 0) {
				if(old_val == 0) {
					return;
				} else {
					val = 0;
				}
			}
			set_hours(task, val, true);
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
			set_hours(task, val, true);
		}
	}

	function setup_group_arrows() {
		$('tr.group img').click(function(e) {
			switch($(this).attr('src')) {
			case '/static/images/collapse.png':
				$(this).attr('src', '/static/images/expand.png');
				groupid = $(this).parents('tr').attr('groupid');
				$('tr.task[groupid=' + groupid + ']').hide();
				break;
			case '/static/images/expand.png':
				$(this).attr('src', '/static/images/collapse.png');
				groupid = $(this).parents('tr').attr('groupid');
				$('tr.task[groupid=' + groupid + ']').show();
				break;
			}
			trigger_list_change();
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
					trigger_group_move(row, new_seq);
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
					trigger_task_change(row, 'taskmove', new_group_id + ':' + new_seq);
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
				task = $(this).parents('tr.task');
				// Switch back to the old span before setting
				$(this).replaceWith($('<span>').text(oldValue).click(editFn));
				set_name(task, text, true);
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

			set_assigned(task, assigned, true);
		});

		$('tr.task img.status', $(table_selector)).contextMenu({
			menu: 'status-menu'
		}, function(action, el, pos) {
			task = $(el).parents('tr.task');
			set_status(task, action, true);
			if(link_hours_status && ['canceled', 'split', 'complete'].indexOf(action) >= 0) {
				set_hours(task, 0, true);
			}
		});

		$('tr.task img.goal', $(table_selector)).contextMenu({
			menu: 'goal-menu'
		}, function(action, el, pos) {
			task = $(el).parents('tr.task');
			set_goal(task, action, true);
		});
	}

	function update_indexes() {
		i = 0;
		$('.task:visible .task-index').each(function() {
			$(this).text(++i);
		});
	}

	function set_name(task, name, trigger) {
		field = $('.name span', task);
		oldValue = field.text();
		field.text(name);
		if(trigger && name != oldValue) {
			trigger_task_change(task, 'name', name);
		}
	}

	function set_hours(task, hours, trigger) {
		field = $('.hours input', task);
		field.val('' + hours);
		if(trigger) {
			trigger_task_change(task, 'hours', val);
		}
		if(link_hours_status) {
			set_status(task, val == 0 ? 'complete' : 'in progress', trigger);
		}
	}

	// assigned is a list
	function set_assigned(task, assigned, trigger) {
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

			trigger_task_change(task, 'assigned', assigned_str);
	}

	function set_status(task, status_name, trigger) {
		node = $('img.status', task);
		id = node.attr('id').replace('status_', '');
		field = $('[name="status[' + id + ']"]');
		if(field.val() != status_name) {
			task.attr('status', status_name);
			field.val(status_name);
			node.attr('src', '/static/images/status-' + status_name.replace(' ', '-') + '.png');
			node.attr('title', status_texts[status_name]);
			if(trigger) {
				trigger_task_change(task, 'status', status_name);
			}
		}
	}

	function set_goal(task, goal_name, trigger) {
		node = $('img.goal', task);
		id = node.attr('id').replace('goal_', '');
		field = $('[name="goal[' + id + ']"]');
		if(field.val() != goal_name) {
			task.attr('goal', goal_name);
			field.val(goal_name);
			node.attr('src', goal_imgs[goal_name]);
			node.attr('title', goal_texts[goal_name]);
			if(trigger) {
				trigger_task_change(task, 'goal', goal_name);
			}
		}
	}

	function delete_task(task_id) {
		row = $('tr.task[taskid=' + task_id + ']');
		if(row) {
			trigger_task_change(row, 'deleted', true);
			if(row.hasClass('selected')) {
				$('.task-index', row).click();
			}
			row.fadeOut();
			row.hide();
			totalTasks--;
			trigger_list_change();
			update_indexes();
		}
	}

	// Triggered when a task field is changed
	// handler args: event, id, field, value
	function on_task_change(handler) {
		$(event_anchor).on('task_change.tasktable', handler);
	}
	function trigger_task_change(task, field, value) {
		$(event_anchor).trigger('task_change.tasktable', [task, field, value]);
	}

	// Triggered when the task list changes. Includes added/removed tasks and changed visibility (filtering)
	// handler args: event
	function on_list_change(handler) {
		$(event_anchor).on('list_change.tasktable', handler);
	}
	function trigger_list_change() {
		$(event_anchor).trigger('list_change.tasktable');
	}

	// Triggered when a group is dragged
	// handler args: group id, new sequence number
	function on_group_move(handler) {
		$(event_anchor).on('group_move.tasktable', handler);
	}
	function trigger_group_move(group, new_seq) {
		$(event_anchor).trigger('group_move.tasktable', [group, new_seq]);
	}

	return {
		init: init,
		update_indexes: update_indexes,
		set_name: set_name,
		set_hours: set_hours,
		set_assigned: set_assigned,
		set_status: set_status,
		set_goal: set_goal,
		delete_task: delete_task,
		on_task_change: on_task_change,
		on_list_change: on_list_change,
		on_group_move: on_group_move,
	};
})();
