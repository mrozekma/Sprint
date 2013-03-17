$(document).ready(function() {
	$('select').chosen();

	all_box = $('#include_all');
	boxes = $('.task-import input[type="checkbox"]').not(all_box);

	box_click = function() {
		all_box.prop('checked', boxes.not(':checked').length == 0);
	}

	all_box.click(function() {
		boxes.off('click');
		boxes.prop('checked', all_box.prop('checked'));
		boxes.click(box_click);
	});

	boxes.click(box_click);
});
