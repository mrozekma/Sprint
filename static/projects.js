$(document).ready(function() {
	$('.show-old-sprints').click(function() {
		$(this).hide();
		project = $(this).parents('.project-summary');
		$('.project-members .member.inactive', project).slideDown();
		$('.old-sprints', project).slideDown();
	});
});
