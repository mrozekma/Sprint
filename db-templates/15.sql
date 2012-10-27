CREATE TABLE searches(id integer not null primary key autoincrement, userid integer CONSTRAINT user REFERENCES users(id), name text, query text, public boolean);
CREATE TABLE search_uses(id integer not null primary key autoincrement, searchid integer CONSTRAINT search REFERENCES searches(id), userid integer CONSTRAINT user REFERENCES users(id));
