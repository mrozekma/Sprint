$(document).ready(function() {
	$('.start-new-note').click(function(e) {
		newNote = $('.new-note', $(this).parents('.notes'));
		newNote.show();
		$('textarea', newNote).focus();
		$(this).hide();
	});

	get_preview = function(obj) {
		note = obj.parents('div.new-note');
		frm = $('form', note);
		$.post(frm.attr('action') + '?dryrun', frm.serialize(), function(data, text, request) {
			$('#preview', note).html(data);
			$('#preview pre code', note).addClass('prettyprint');
			prettyPrint();
		});
	};

	$('div.new-note .text .body textarea')
		.bind('paste', function() {obj = $(this); setTimeout(function() {get_preview(obj);}, 0)})
		.typing({delay: 400, stop: function(e, obj) {get_preview(obj);}});

	$('a#undelete').click(function() {
		lnk = $(this);
		frm = lnk.parents('form');
		$.post(frm.attr('action'), frm.serialize(), function(data, text, request) {
			switch(request.status) {
			case 200:
			case 298:
			default:
				lnk.replaceWith($("<span>").text("Unable to undelete: " + data));
				break;
			case 299:
				document.location.reload(true);
				break;
			}
		});
	});
});
