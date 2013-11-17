$.noty.defaults.theme = 'sprint';
$.noty.defaults.layout = 'bottomCenter';
$.noty.defaults.timeout = 0;

function showChangelog(html) {
	noty({text: html});
}
