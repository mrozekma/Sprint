$(document).ready(function() {
	$('select').chosen();
	$('#save-button').click(function(e) {
		e.preventDefault();
        e.stopImmediatePropagation();
		$.post($('form').attr('action'), $('form').serialize(), function(data, text, request) {
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
				box.attr('class', 'tint green');
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
});
