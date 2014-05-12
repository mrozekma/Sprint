$(document).ready(function() {
	$('img.autolink_icon').contextMenu({
		menu: 'autolink_icons'
	}, function(action, el, pos) {
		$('input[type=hidden]', $(el).parent('td')).val(action);
		$(el).attr('src', '/static/images/' + action + '.png');
	});
});
