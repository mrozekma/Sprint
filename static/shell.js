function term_process(command, term) {
	$.post('/shell/run', {
		mode: this.mode || '',
		command: command,
		path: window.location.pathname + window.location.search
	}, function(data, text, request) {
		if('error' in data) {
			term.error(data['error']);
		} else {
			if('mode' in data) {
				if(data['mode'] === false) {
					term.pop();
				} else {
					term.push(term_process, {
						prompt: (data['prompt'] || data['mode']) + ' ',
						mode: data['mode']
					});
				}
			}

			if('output' in data) {
				$.each(data['output'].split('\n'), function() {
					term.echo(this);
				});
			}

			if('redirect' in data) {
				window.location = data['redirect'];
			}
		}
	}, 'json');
}

function term_toggle(term) {
	visible = !term.is(':visible');
	term.slideToggle('fast');
	term.focus(focus = visible);
	term.set_command('');
}

$(document).ready(function() {
	// Start logged in
    $.Storage.set('token_shell', 'token');
    $.Storage.set('login_shell', 'user');

	term = $('#shell');
	term.hide().terminal(term_process, {
		name: 'shell',
		prompt: '$ ',
		height: 100,
		enabled: false,
		greetings: '',
		login: function(user, password, cb) { // onBeforelogout should prevent this from ever happening
			throw "Unexpected login attempt";
		},
		onBeforelogout: function() {
			term_toggle(term);
			return false;
		}
	});

	$(document).keypress(function(e) {
		if(!e.ctrlKey && !e.altKey && !e.shiftKey && e.which == 96) { // `
			term_toggle(term);
		}
	});
});
