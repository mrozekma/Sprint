$(document).ready(function() {
	// up, down, left, right
	// 38, 40, 37, 39

	hist = [];
	hist_index = -1;

	$('input#input').keydown(function(e) {
		switch(e.keyCode) {
		case 13: // Enter
			hist_index = -1;
			$.post('/admin/repl', {code: $(this).val()}, function(dataL, text, request) {
				if(!(dataL instanceof Array)) {
					dataL = [dataL];
				}

				hist.push($('input#input').val());
				$('input#input').val('');

				$.each(dataL, function(index, data) {
					v = $('#variables > .box-wrapper');
					$('.elem:not(.header), .clear', v).remove();
					$.each(data['vars'], function(index, arr) {
						v.append($('<div>').addClass('clear'));
						v.append($('<div>').addClass('elem').text(arr[0]));
						v.append($('<div>').addClass('elem').text(arr[1]));
						v.append($('<div>').addClass('elem').html(arr[2]));
					});

					c = $('#console > pre');
					c.append($('<div>').addClass('repl-code').html("&gt;&nbsp;" + data.code));
					if(data.stdout != '') {
						c.append($('<div>').addClass('repl-stdout').text(data.stdout));
					}
					if(data.stderr != '') {
						c.append($('<div>').addClass('repl-stderr').append($("<b>").text(data.stderr[0])).append($("<span>").text(": " + data.stderr[1])));
					}
					c[0].scrollTop = c[0].scrollHeight;
				});
			}, 'json');
			break;
		case 27: // Esc
			hist_index = -1;
			$('input#input').val('');
			break;
		case 38: // Up
			if(hist_index < 0) {
				hist_index = hist.length;
				if($('input#input').val() != '') {
					hist.push($('input#input').val());
				}
			}

			if(hist_index > 0) {
				$('input#input').val(hist[--hist_index]);
			}

			e.preventDefault();
			e.stopImmediatePropagation();
			break;
		case 40: // Down
			if(++hist_index == hist.length) {
				hist_index = -1;
				$('input#input').val('');
			} else {
				$('input#input').val(hist[hist_index]);
			}

			e.preventDefault();
			e.stopImmediatePropagation();
			break;
		}
	});
});
