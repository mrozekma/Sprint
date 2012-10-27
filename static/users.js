$(document).ready(function() {
	get_preview = function(obj) {
		frm = $('form#message-form');
		$.post(frm.attr('action') + '?dryrun', frm.serialize(), function(data, text, request) {
			$('#preview', frm).html(data);
			$('#preview pre code', frm).addClass('prettyprint');
			prettyPrint();
		});
	};

	$('form#message-form textarea')
		.bind('paste', function() {obj = $(this); setTimeout(function() {get_preview(obj);}, 0)})
		.typing({delay: 400, stop: function(e, obj) {get_preview(obj);}});
});