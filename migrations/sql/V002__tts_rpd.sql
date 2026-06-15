CREATE SCHEMA IF NOT EXISTS tts;

CREATE TABLE IF NOT EXISTS tts.gemini_key_rpd (
    key_tail TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    remaining INTEGER NOT NULL
);
