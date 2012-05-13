ALTER TABLE sprints ADD ownerid integer CONSTRAINT owner REFERENCES users(id);
UPDATE sprints SET ownerid = (SELECT ownerid FROM projects WHERE id = projectid);

-- Are you kidding, sqlite? You can't drop columns?
ALTER TABLE projects RENAME TO projects_old;
CREATE TABLE projects(id integer not null primary key autoincrement, name string);
INSERT INTO projects SELECT id, name FROM projects_old;
DROP TABLE projects_old;
