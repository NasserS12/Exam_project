DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS chapters;

CREATE TABLE chapters (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    text TEXT NOT NULL,
    option_1 TEXT NOT NULL,
    option_2 TEXT NOT NULL,
    option_3 TEXT NOT NULL,
    option_4 TEXT NOT NULL,
    answer TEXT NOT NULL,
    CHECK(answer IN (option_1,option_2,option_3,option_4))
);