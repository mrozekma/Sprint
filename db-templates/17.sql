CREATE TABLE retrospective_categories(id integer not null primary key autoincrement, sprintid integer CONSTRAINT sprint REFERENCES sprints(id), name text);
CREATE TABLE retrospective_entries(id integer not null primary key autoincrement, catid integer CONSTRAINT cat REFERENCES retrospective_categories(id), body text, good boolean);
