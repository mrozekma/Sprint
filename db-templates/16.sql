CREATE TABLE assigned(taskid integer not null CONSTRAINT task REFERENCES tasks(id), revision integer not null, userid integer not null CONSTRAINT user REFERENCES users(id), primary key(taskid, revision, userid));
INSERT INTO assigned SELECT id, revision, coalesce(assignedid, 0) FROM tasks;
ALTER TABLE tasks RENAME TO tasks_old;
CREATE TABLE tasks(id integer not null, revision integer not null, seq integer, groupid integer CONSTRAINT 'group' REFERENCES groups(id), sprintid integer CONSTRAINT sprint REFERENCES sprints(id), creatorid integer CONSTRAINT creator REFERENCES users(id) ON DELETE RESTRICT ON UPDATE RESTRICT, goalid integer CONSTRAINT goal REFERENCES goals(id), name text, status text, hours integer, timestamp integer, deleted boolean, primary key(id, revision));
INSERT INTO tasks SELECT id, revision, seq, groupid, sprintid, creatorid, goalid, name, status, hours, timestamp, deleted FROM tasks_old;
DROP TABLE tasks_old;
