$(document).ready(function () {
	$('.defaultfocus').focus();

	$('.box.collapsible .title').click(function(event) {
		$(this).parents('.box.collapsible').toggleClass('expanded');
	});
});

$.expr[":"].econtains = function(obj, index, meta, stack) {
	return (obj.textContent || obj.innerText || $(obj).text() || "").toLowerCase() == meta[3].toLowerCase();
}

function hltable_over(row) {
	row.className = 'hl_on';
}

function hltable_out(row) {
	row.className = 'hl_off';
}

function hltable_click(url) {
	document.location = url;
}
