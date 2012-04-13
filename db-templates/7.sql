CREATE TABLE prefs(id integer not null primary key autoincrement, userid integer not null CONSTRAINT user REFERENCES users(id), defaultSprintTab text);
CREATE TABLE prefs_backlog_styles(id integer not null primary key autoincrement, userid integer not null CONSTRAINT user REFERENCES users(id), status text, style text);
