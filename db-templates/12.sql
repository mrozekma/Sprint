CREATE TABLE messages(id integer not null primary key autoincrement, userid integer CONSTRAINT user REFERENCES users(id), senderid integer, title text, body text, language text, timestamp integer, read boolean default 0);
CREATE TABLE prefs_messages(id integer not null primary key autoincrement, userid integer CONSTRAINT user REFERENCES users(id), type text, enabled boolean);
INSERT INTO prefs_messages(userid, type, enabled) SELECT id AS userid, 'sprintMembership' AS type, 0 AS enabled FROM users;
INSERT INTO prefs_messages(userid, type, enabled) SELECT id AS userid, 'taskAssigned' AS type, 0 AS enabled FROM users;
INSERT INTO prefs_messages(userid, type, enabled) SELECT id AS userid, 'note' AS type, 1 AS enabled FROM users;
INSERT INTO prefs_messages(userid, type, enabled) SELECT id AS userid, 'priv' AS type, 1 AS enabled FROM users;
