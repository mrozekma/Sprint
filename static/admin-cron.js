$(document).ready(function() {
	$.post("/admin/cron/run-bg", {'name': job_name}, function(data, text, request) {
		$('#output').text(data);
		if(request.status == 299) {
			// Wait a moment for the cron job to hopefully get the #reqcheck lock
			setTimeout(function() {
				// Will block until the job finishes
				document.location = '/admin/cron';
			}, 1000);
		}
	});
});
