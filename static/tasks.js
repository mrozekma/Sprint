$(document).ready(function() {
	$('.notes .note .text .body pre code').addClass('prettyprint');
	prettyPrint();

	$('.start-new-note').click(function(e) {
		newNote = $('.new-note', $(this).parents('.notes'));
		newNote.show();
		$('textarea', newNote).focus();
		$(this).hide();
	});

	get_preview = function(obj) {
		note = obj.parents('div.new-note');
		frm = $('form', note);
		console.log(frm.serialize())
		$.post(frm.attr('action') + '?dryrun', frm.serialize(), function(data, text, request) {
			$('#preview', note).html(data);
			$('#preview pre code', note).addClass('prettyprint');
			prettyPrint();
		});
	};

	$('div.new-note .text .body textarea')
		.bind('paste', function() {obj = $(this); setTimeout(function() {get_preview(obj);}, 0)})
		.typing({delay: 400, stop: function(e, obj) {get_preview(obj);}});
});
