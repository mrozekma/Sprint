CREATE TABLE settings(id integer not null primary key autoincrement, name text, value text);
CREATE TABLE users(id integer not null primary key autoincrement, username text, password text);
CREATE TABLE privileges(id integer not null primary key autoincrement, name text, description text, arguments integer);
CREATE TABLE grants(id integer not null primary key autoincrement, userid integer, privid integer, arguments string);
CREATE TABLE projects(id integer not null primary key autoincrement, ownerid integer, name string);
CREATE TABLE sprints(id integer not null primary key autoincrement, projectid int, name text, start integer, end integer);
CREATE TABLE members(sprintid integer, userid integer, primary key(sprintid, userid) on conflict replace);
CREATE TABLE groups(id integer not null primary key autoincrement, sprintid integer, seq integer, name text, deletable boolean default true);
CREATE TABLE goals(id integer not null primary key autoincrement, sprintid int constraint sprint references sprints(id) on delete cascade on update cascade, name text, color text);
CREATE TABLE tasks(id integer not null, revision integer not null, seq integer, groupid integer CONSTRAINT 'group' REFERENCES groups(id), sprintid integer CONSTRAINT sprint REFERENCES sprints(id), creatorid integer CONSTRAINT creator REFERENCES users(id) ON DELETE RESTRICT ON UPDATE RESTRICT, assignedid integer CONSTRAINT assigned REFERENCES users(id) ON DELETE RESTRICT ON UPDATE RESTRICT, goalid integer CONSTRAINT goal REFERENCES goals(id), name text, status text, hours integer, timestamp integer, primary key(id, revision));

INSERT INTO privileges(name, description, arguments) VALUES('User', 'Privilege all registered users have', 0);
INSERT INTO privileges(name, description, arguments) VALUES('Dev', 'Allows access to features marked incomplete', 0);
