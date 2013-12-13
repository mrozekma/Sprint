$(document).ready(function() {
	$.post("/admin/cron/run-bg", {'name': job_name}, function(data, text, request) {
		$('#output').text(data);
		if(request.status == 299) {
			document.location = '/admin/cron'; // will block until the job finishes
		}
	});
});
