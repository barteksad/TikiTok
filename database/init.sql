CREATE DATABASE tiktok;
GRANT ALL PRIVILEGES ON DATABASE tiktok TO postgres;

\connect tiktok

CREATE TABLE video
(
    id             VARCHAR(50)  PRIMARY KEY,
    title          VARCHAR(255) NOT NULL,
    likes_count    INTEGER      NOT NULL DEFAULT 0,
    status         VARCHAR(16)  NOT NULL DEFAULT 'WAITING',
    class          SMALLINT,
    time_processed TIMESTAMP,

    CHECK ((time_processed IS NULL AND status = 'WAITING' AND class IS NULL)
        OR (time_processed IS NOT NULL AND status = 'PROCESSED' AND class BETWEEN 0 AND 599)
        OR (time_processed IS NOT NULL AND status = 'INVALID' AND class IS NULL)
    ),

    CHECK (likes_count >= 0)
);

CREATE INDEX idx_videos_lookup ON video (class, time_processed);