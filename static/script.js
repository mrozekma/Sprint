$(document).ready(function () {
	$('.defaultfocus').focus();

	$('.box.collapsible .title').click(function(event) {
		$(this).parents('.box.collapsible').toggleClass('expanded');
	});

	$('.alert-message .close').click(function() {
		hidebox($(this).parents('.alert-message'), 0);
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
		console.log(box);
		console.log($(box));
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
