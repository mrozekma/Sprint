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
	$.get(document.location.pathname + '/chart-data', {assigned: assigned.join(',')}, function(data, textStatus, xhr) {
		chart = Highcharts.charts[0];
		while(chart.series.length > 0) {
			chart.series[0].remove(false);
		}
		for(i in data) {
			chart.addSeries(data[i], false);
		}
		chart.redraw();

		console.log(assigned);
		console.log(assigned[0]);
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
	}, 'json');
}
