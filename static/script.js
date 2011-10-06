$(document).ready(function () {
	$('.defaultfocus').focus();

	$('.box.collapsible .title').click(function(event) {
		$(this).parents('.box.collapsible').toggleClass('expanded');
	});
});

$.expr[":"].econtains = function(obj, index, meta, stack) {
	return (obj.textContent || obj.innerText || $(obj).text() || "").toLowerCase() == meta[3].toLowerCase();
}

$.extend($.fn, {
	savebutton: function(box, next_url) {
		console.log($(this));
		$(this).click(function(e) {
			console.log($(this));
			e.preventDefault();
			e.stopImmediatePropagation();
			form = $(this).parents('form');
			$.post(form.attr('action'), form.serialize(), function(data, text, request) {
				switch(request.status) {
				case 200:
					box.attr('class', 'tint red');
					$('span', box).html(data);
				case 298:
					box.attr('class', 'tint yellow');
					$('span', box).html(data);
					break;
				case 299:
					if(next_url == undefined) {
						box.attr('class', 'tint green');
						$('span', box).html(data);
					} else if(next_url == '') {
						window.location = data;
					} else if(typeof next_url == 'function') {
						next_url(data);
					} else {
						window.location = next_url;
						return;
					}
				default:
					box.attr('class', 'tint blood');
					$('span', box).html("Unexpected response code " + request.status)
					break;
				}

				box.fadeIn();
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
