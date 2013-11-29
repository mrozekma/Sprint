$(document).ready(function() {
	$('.retrospective .entry').each(function() {
		update($(this));
	});

	if(editing) {
		$('.retrospective').on('click', '.entry div', function(e) {
			$('textarea', $(this).parent('.entry')).addClass('active').show().focus();
			$(this).remove();
			e.stopPropagation();
		}).on('click', '.entry textarea', function(e) {
			e.stopPropagation();
		}).on('click', '.entry', function(e) {
			$(this).toggleClass('good bad');
			if($(this).data('id') != 'new') {
				update($(this), undefined, $(this).hasClass('good'));
			}
		}).on('focus', '.entry textarea', function() {
			$(this).addClass('active');
		}).on('blur', '.entry textarea', function() {
			$(this).removeClass('active');
			entry = $(this).parent('.entry');
			body = $(this).val();
			if(entry.data('id') != 'new' || body.replace(/^\s+|\s+$/g, '') != '') {
				update(entry, body, entry.hasClass('good'));
			}
		}).on('keyup', '.entry textarea', function(e) {
			// Enter finishes editing; Shift+Enter inserts a newline
			if(e.keyCode == 13 && !e.shiftKey) {
				$(this).blur();
			}
		});

		$('.retrospective .category').each(function() {
			insert_new($(this));
		});
	}
});

function insert_new(category) {
	category.append($('<div class="entry good" data-id="new"><textarea></textarea></div>'));
}

// this also renders; if 'body' or 'good' are undefined they won't be updated
function update(entry, body, good) {
	$('textarea', entry).hide();
	$('div', entry).remove();
	entry.removeClass('good bad').addClass('loading');
	$.post('/sprints/' + sprint_id + '/retrospective/render', {
		'id': entry.data('id'),
		'catid': entry.parent('.category').data('id'),
		'body': body,
		'good': good
	}, function(data, status, xhr) {
		if(data['deleted']) {
			entry.remove();
			return;
		}
		entry.append($('<div/>').html(data.body)).removeClass('loading').addClass(data.good ? 'good' : 'bad');
		$('pre code', entry).addClass('prettyprint');
		prettyPrint();
		if(entry.data('id') == 'new') {
			entry.data('id', data.id);
		}
	}, 'json');
	if(entry.data('id') == 'new') {
		insert_new(entry.parent('.category'));
	}
	$('.entry[data-id=new] textarea', entry.parent('.category')).focus();
}
