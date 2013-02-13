$(document).ready(function() {
	$('select[name="status"]').change(function() {
		hours = $('input[name="hours"]');
		if($(this).val() == 'deferred' && hours.val() == '') {
			hours.val('0');
		}
	});
});
