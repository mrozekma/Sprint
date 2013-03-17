$(document).ready(function() {
	$('select').chosen();

	all_box = $('#include_all');
	boxes = $('.task-import input[type="checkbox"]').not(all_box);

	update_included = function() {
		$('input[name=included]').val($.makeArray(boxes.filter(':checked').map(function() {
			return $(this).data('id');
		})).join(','));
	};

	box_click = function() {
		all_box.prop('checked', boxes.not(':checked').length == 0);
		update_included();
	}

	all_box.click(function() {
		boxes.off('click');
		boxes.prop('checked', all_box.prop('checked'));
		update_included();
		boxes.click(box_click);
	});

	boxes.click(box_click);
});
