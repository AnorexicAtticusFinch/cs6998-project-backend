CREATE TABLE referral_requests(
    sid VARCHAR(200),
    aid VARCHAR(200),
    timestamp INT,
    status VARCHAR(200) NOT NULL,
    PRIMARY KEY (sid, aid, timestamp),
)

CREATE TABLE chat_check(
    sid VARCHAR(200),
    aid VARCHAR(200),
    counter INT DEFAULT 1,
    PRIMARY KEY (sid, aid),
)

CREATE TABLE referral_requests(sid VARCHAR(200),aid VARCHAR(200),timestamp INT,status VARCHAR(200) NOT NULL,PRIMARY KEY (sid, aid, timestamp))

CREATE TABLE chat_check(sid VARCHAR(200),aid VARCHAR(200),counter INT DEFAULT 1,PRIMARY KEY (sid, aid))

INSERT INTO referral_requests VALUES('s1', 'a1', 1, 'pending')
(('s1', 'a1', 1, 'pending'),)
