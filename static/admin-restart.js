function checkUp() {
	console.log('checking...');
	$.ajax({
		url: '/',
		success: function() {
			document.location = '/admin/info';
		},
		error: function() {
			setTimeout(checkUp, 1000);
		}
	});
}

$(document).ready(function() {
	$.post('/admin/restart?now');
	setTimeout(checkUp, 1000);
});
