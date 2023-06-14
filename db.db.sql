BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "connection" (
	"login"	TEXT,
	"password"	TEXT
);
CREATE TABLE IF NOT EXISTS "keys" (
	"login"	TEXT,
	"key_val"	TEXT,
	"desc"	INTEGER
);
COMMIT;
