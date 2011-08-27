$(document).ready(function() {
	$('select:not([disabled])').chosen();

	$('#save-button').click(function(e) {
		e.preventDefault();
        e.stopImmediatePropagation();
		$.post($('form').attr('action'), $('form').serialize(), function(data, text, request) {
			box = $('#post-status')
			switch(request.status) {
			case 200:
				box.attr('class', 'tint red');
				$('span', box).html(data);
			case 298:
				box.attr('class', 'tint yellow');
				$('span', box).html(data);
				break;
			case 299:
				// box.attr('class', 'tint green');
				// $('span', box).html(data);
				window.location = next_url;
				return;
			default:
				box.attr('class', 'tint blood');
				$('span', box).html("Unexpected response code " + request.status)
				break;
			}

			box.fadeIn();
		});
	});

	$('#cancel-button').click(function(e) {
		e.preventDefault();
        e.stopImmediatePropagation();
		window.location = next_url;
	});

	get_preview = function() {
		$.post($('form').attr('action') + '&dryrun=true', $('form').serialize(), function(data, text, request) {
			$('#preview').html(data);
		});
	};

	$('#many-body').bind('paste', function() {setTimeout(get_preview, 0)}).typing({delay: 400, stop: get_preview});
});
