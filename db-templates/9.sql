CREATE TABLE log(id integer not null primary key autoincrement, timestamp real, userid integer CONSTRAINT user REFERENCES users(id), ip text, location text, type text, text text);
