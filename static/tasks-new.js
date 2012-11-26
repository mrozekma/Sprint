$(document).ready(function() {
	$('select:not([disabled])').chosen();
	$('#save-button').savebutton($('#post-status'), next_url);
	$('#cancel-button').cancelbutton(next_url);

	get_preview = function() {
		$.post($('form').attr('action') + '&dryrun=true', $('form').serialize(), function(data, text, request) {
			$('#post-status').hide();
			$('#preview').html(data);
		});
	};

	$('#many-body').bind('paste', function() {setTimeout(get_preview, 0)}).typing({delay: 400, stop: get_preview});
});
