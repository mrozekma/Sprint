UPDATE prefs_messages SET type = 'noteMention' WHERE type = 'note';
INSERT INTO prefs_messages(userid, type, enabled) SELECT id, 'noteRelated', 1 FROM users;
