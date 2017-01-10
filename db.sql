CREATE TABLE admin(
	username VARCHAR(10) PRIMARY KEY,
	password VARCHAR(100) NOT NULL
);

CREATE TABLE series(
	series_name VARCHAR(50) PRIMARY KEY
);

CREATE TABLE series_text(
	series_name VARCHAR(50),
	desccription TEXT
);

# Dummy data for admin using hashed password, 'username':'admin', 'password':'admin'
INSERT INTO admin VALUES('admin', 'pbkdf2:sha1:1000$nUbfE1Ja$d502082c40df4d9807e4728e77205b5dd58f600f');