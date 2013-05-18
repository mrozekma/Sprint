function setup_filter_buttons() {
	$('#filter-assigned a:gt(0)').click(function(e) {
		if(e.ctrlKey) {
			$(this).toggleClass('selected');
		} else {
			$('#filter-assigned a').removeClass('selected');
			$(this).addClass('selected');
		}

		apply_filters();
		return false;
	});

	$('#filter-assigned a:first').click(function(e) {
		$('#filter-assigned a').removeClass('selected');
		apply_filters();
		return false;
	});
}

function apply_filters() {
	var assigned = $.makeArray($('#filter-assigned .selected').map(function () {return $(this).attr('assigned');}));
	var show_ids;
	if(assigned.length == 0) {
		show_ids = true;
	} else {
		show_ids = {}
		$.each(assigned, function() {
			$.each(tasks_by_assigned[this], function() {
				show_ids[this] = true;
			});
		});
	}

	chart = Highcharts.charts[0];
	for(i in chart.series) {
		id = parseInt(chart.series[i].name.slice(0, chart.series[i].name.indexOf(':')), 10);
		chart.series[i].setVisible(show_ids === true || id in show_ids, false);
	}
	chart.redraw();

	entries = $('.revision-history .revision-entry');
	days = $('.revision-history .daymarker');
	if(assigned.length == 0) {
		entries.show();
		days.show();
	} else {
		entries.hide();
		$.each(assigned, function() {
			entries.filter('[assigned~="' + this + '"]').show();
		});

		// Hide day markers with no entries
		days.show();
		days.each(function() {
			seek = $(this);
			while(seek = seek.next()) {
				if(seek.is('.revision-entry:visible')) {
					return;
				} else if(seek.length ==0 || seek.hasClass('daymarker')) {
					$(this).hide();
					return;
				}
			}
		});
	}
}
