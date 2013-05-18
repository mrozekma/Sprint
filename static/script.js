$(document).ready(function () {
	$('.defaultfocus').focus();

	$('.box.collapsible .title').click(function(event) {
		$(this).parents('.box.collapsible').toggleClass('expanded');
	});

	$('.alert-message .close').click(function() {
		hidebox($(this).parents('.alert-message'), 0);
	});

	closeSearchBox = function() {
		$('#saved-searches').remove();
	}

	$('.topmenu a:contains("Search")').click(function(e) {
		e.preventDefault();
		e.stopImmediatePropagation();

		if($('#saved-searches').length > 0) {
			$('#saved-searches').remove();
			$(document).unbind('click', closeSearchBox);
		} else {
			box = $('<div/>')
				.attr('id', 'saved-searches')
				.css({
					left: $(this).position().left,
					top: $(this).position().top + 30,
				})
				.append($('<img/>').attr('src', '/static/images/loading.gif'))
				.appendTo($('.topmenu'));

			$.get('/search/saved/menubox', function(data) {
				sprintArg = (typeof sprintid === 'undefined') ? '' : '/' + sprintid;

				box.empty();

				$('<h1>Your saved searches</h1>')
					.append($('<a />').attr('class', 'right').attr('href', '/search/saved').text('(edit)'))
					.appendTo(box);
				if(data['yours'].length == 0) {
					box.append($('<i>None</i>'));
				} else {
					for(i in data['yours']) {
						search = data['yours'][i];
						box.append($('<a />').attr('href', '/search/saved/' + search['id'] + '/run' + sprintArg).text(search['name']).attr('title', search['query']));
						box.append($('<br />'));
					}
				}

				$("<h1>Other users' saved searches</h1>")
					.append($('<a />').attr('class', 'right').attr('href', '/search/saved/others').text('(edit)'))
					.appendTo(box);
				if(data['others'].length == 0) {
					box.append($('<i>None followed (' + data['otherTotal'] + ' available)</i>'));
				} else {
					for(i in data['others']) {
						search = data['others'][i];
						box.append($('<a />').attr('href', '/search/saved/' + search['id'] + '/run' + sprintArg).text(search['name']).attr('title', search['query']));
						box.append($('<img />').attr('class', 'gravatar').attr('src', search['gravatar']).attr('title', search['username']));
						box.append($('<br />'));
					}
				}
			}, 'json');

			$(document).click(closeSearchBox);
		}
	});
});

$.expr[":"].econtains = function(obj, index, meta, stack) {
	return (obj.textContent || obj.innerText || $(obj).text() || "").toLowerCase() == meta[3].toLowerCase();
}

$.extend($.fn, {
	savebutton: function(box, next_url) {
		$(this).click(function(e) {
			e.preventDefault();
			e.stopImmediatePropagation();
			form = $(this).parents('form');
			$.post(form.attr('action'), form.serialize(), function(data, text, request) {
				switch(request.status) {
				case 200:
					box.attr('class', 'alert-message error');
					$('span.boxbody', box).html(data);
					break;
				case 298:
					box.attr('class', 'alert-message warning');
					$('span.boxbody', box).html(data);
					break;
				case 299:
					console.log("299 (-> " + next_url + "): " + data);
					if(next_url == undefined) {
						box.attr('class', 'alert-message success');
						$('span.boxbody', box).html(data);
						break;
					} else if(next_url == '') {
						window.location = data;
					} else if(typeof next_url == 'function') {
						next_url(data);
					} else {
						window.location = next_url;
					}
					return;
				default:
					box.attr('class', 'alert-message error');
					$('span.boxbody', box).html("Unexpected response code " + request.status)
					break;
				}

				showbox(box);
			});
		});
	},

	cancelbutton: function(next_url) {
		$(this).click(function(e) {
			e.preventDefault();
			e.stopImmediatePropagation();
			window.location = next_url;
		});
	}
});

function hltable_over(row) {
	row.className = 'hl_on';
}

function hltable_out(row) {
	row.className = 'hl_off';
}

function hltable_click(url) {
	document.location = url;
}

function showbox(box) {
	$(box).show().css('opacity', 100);
}

function hidebox(box, timeout) {
	if(timeout == 0) {
		if($(box).hasClass('fixed')) {
			$(box).animate({opacity: 0});
		} else {
			$(box).fadeOut();
		}
	} else {
		setTimeout(function() {hidebox(box, 0);}, timeout * 1000);
	}
}

function buildmode(mode) {
	$.post('/admin/build', {'mode': mode}, function(data, text, request) {
		window.location.reload(true);
	});
}

function unimpersonate() {
	$.post('/admin/unimpersonate', {}, function(data, text, request) {
		window.location.reload(true);
	});
}
