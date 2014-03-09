$(document).ready(function() {
	$('select:not([disabled])').chosen();
	$('#save-button').savebutton($('#post-status'), next_url);
	$('#cancel-button').cancelbutton(next_url);

	get_preview = function() {
		$.post($('form#write-tasks').attr('action') + '&dryrun=true', $('form#write-tasks').serialize(), function(data, text, request) {
			$('#post-status').hide();
			$('#preview').html(data);
		});
	};

	if($('#many-body').length > 0) {
		$('#many-body').bind('paste', function() {setTimeout(get_preview, 0)}).typing({delay: 400, stop: get_preview});
	}

	$('form#upload-tasks input[type=file]').change(function() {
		$(this).parent('form').submit();
	});

	get_preview();
});
