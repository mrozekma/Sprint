CREATE TABLE changelog_views(id integer not null primary key autoincrement, changeid integer not null, userid integer not null CONSTRAINT user REFERENCES users(id), timestamp int not null);
