CREATE DATABASE tiktok;
GRANT ALL PRIVILEGES ON DATABASE tiktok TO postgres;

\connect tiktok

CREATE TABLE video
(
    id             VARCHAR(50)  PRIMARY KEY,
    title          VARCHAR(255) NOT NULL,
    likes_count    INTEGER      NOT NULL DEFAULT 0,
    status         VARCHAR(16)  NOT NULL DEFAULT 'WAITING',
    class1         SMALLINT,
    class2         SMALLINT,
    class3         SMALLINT,
    time_processed TIMESTAMP,

    CHECK ((time_processed IS NULL
                AND status = 'WAITING'
                AND class1 IS NULL
                AND class2 IS NULL
                AND class3 IS NULL)
        OR (time_processed IS NOT NULL
                AND status = 'INVALID'
                AND class1 IS NULL
                AND class2 IS NULL
                AND class3 IS NULL)
        OR (time_processed IS NOT NULL
                AND status = 'PROCESSED'
                AND class1 BETWEEN 0 AND 599
                AND class2 BETWEEN 0 AND 599
                AND class3 BETWEEN 0 AND 599)
    ),

    CHECK (likes_count >= 0)
);

CREATE INDEX idx_videos_lookup1 ON video (class1, time_processed);
CREATE INDEX idx_videos_lookup2 ON video (class2, time_processed);
CREATE INDEX idx_videos_lookup3 ON video (class3, time_processed);

CREATE TABLE likes
(
    video_id   VARCHAR(50) NOT NULL,
    FOREIGN KEY (video_id) REFERENCES video (id),
    user_id    VARCHAR(50) NOT NULL,
    CONSTRAINT likes_pk PRIMARY KEY (video_id, user_id)
);

CREATE TABLE preferences
(
    user_id    VARCHAR(50) PRIMARY KEY,
    vector     REAL[600]  NOT NULL
);