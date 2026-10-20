-- Safe to run on every deploy: each statement only adds what is missing.

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL
);

ALTER TABLE chapters ADD COLUMN IF NOT EXISTS subject_id INTEGER REFERENCES subjects(id);
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS position INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS chapters_subject_name ON chapters (subject_id, name);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    text TEXT NOT NULL,
    option_1 TEXT NOT NULL,
    option_2 TEXT NOT NULL,
    option_3 TEXT,
    option_4 TEXT,
    answer TEXT NOT NULL,
    CHECK (answer IN (option_1, option_2, option_3, option_4))
);

-- Questions can have 2 to 4 options (true/false has 2).
ALTER TABLE questions ALTER COLUMN option_3 DROP NOT NULL;
ALTER TABLE questions ALTER COLUMN option_4 DROP NOT NULL;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_page INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS questions_chapter_text ON questions (chapter_id, text);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (score >= 0 AND score <= total)
);
