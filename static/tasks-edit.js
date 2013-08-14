$(document).ready(function() {
	$('select:not([disabled])').chosen();
	$('select[name="status"]').change(function() {
		hours = $('input[name="hours"]');
		if($(this).val() == 'deferred' && hours.val() == '') {
			hours.val('0');
		}
	});
});
