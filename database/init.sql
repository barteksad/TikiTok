CREATE DATABASE tiktok;
GRANT ALL PRIVILEGES ON DATABASE tiktok TO postgres;

\connect tiktok
CREATE TABLE video (
    id VARCHAR (50) PRIMARY KEY
);