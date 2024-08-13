import sqlite3

class Database:

    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
        self.initialize_tables()

    def initialize_tables(self):
        # Create user table
        user_table = """
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            interests TEXT NOT NULL
        );
        """
        self.cursor.execute(user_table)
        self.connection.commit()

        # Create video table
        video_table = """
        CREATE TABLE IF NOT EXISTS video (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            video_id TEXT NOT NULL,
            user_id INTEGER,
            parent_classification TEXT,
            classification TEXT,
            reaction TEXT,
            reason TEXT,
            execution_time TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
        """
        self.cursor.execute(video_table)
        self.connection.commit()

        # Create video metadata table
        video_metadata_table = """
        CREATE TABLE IF NOT EXISTS video_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            tags TEXT NOT NULL,
            playtime TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            youtube_category TEXT NOT NULL,
            youtube_topics TEXT NOT NULL,
            FOREIGN KEY (video_id) REFERENCES video(video_id)
        );
        """
        self.cursor.execute(video_metadata_table)
        self.connection.commit()



    def insert_user(self, id, email, password, interests):
        insert_query = """
            INSERT OR IGNORE INTO user (id, email, password, interests)
            VALUES (?, ?, ?, ?);
            """
        self.cursor.execute(insert_query, (id, email, password, interests))
        self.connection.commit()

    def insert_video(self, url, video_id, user_id, parent_classification, classification, reaction, reason, execution_time, timestamp):
        insert_query = """
            INSERT INTO video (url, video_id, user_id, parent_classification, classification, reaction, reason, execution_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
        self.cursor.execute(insert_query, (url, video_id, user_id, parent_classification, classification, reaction, reason, execution_time, timestamp))
        self.connection.commit()

    def insert_video_metadata(self, video_id, title, description, tags, playtime, channel_name, youtube_category, youtube_topics):
        insert_query = """
            INSERT INTO video_metadata (video_id, title, description, tags, playtime, channel_name, youtube_category, youtube_topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """
        self.cursor.execute(insert_query, (video_id, title, description, tags, playtime, channel_name, youtube_category, youtube_topics))
        self.connection.commit()

    def get_user(self, id):
        select_query = """
            SELECT * FROM user WHERE id = ?;
            """
        self.cursor.execute(select_query, (id,))
        return self.cursor.fetchone()

    def get_video(self, video_id):
        select_query = """
            SELECT * FROM video WHERE video_id = ?;
            """
        self.cursor.execute(select_query, (video_id,))
        return self.cursor.fetchone()

    def get_videos_sorted_by_oldest(self, user_id):
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        select_query = """
            SELECT * FROM video WHERE user_id = ? ORDER BY timestamp ASC;
            """
        self.cursor.execute(select_query, (user_id,))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_videos_sorted_by_oldest_with_metadata(self, user_id):
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        select_query = """
            SELECT * FROM video 
            LEFT JOIN video_metadata ON video.id = video_metadata.id
            WHERE user_id = ? ORDER BY timestamp ASC;
            """
        self.cursor.execute(select_query, (user_id,))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_last_video_id_seen(self, user_id):
        select_query = """
            SELECT video_id FROM video WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1;
            """
        self.cursor.execute(select_query, (user_id,))
        return self.cursor.fetchone()

    def get_last_video_id(self, user_id):
        select_query = """
            SELECT video_id FROM video WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1;
            """
        self.cursor.execute(select_query, (user_id,))
        return self.cursor.fetchone()

    def has_seen_video(self, user_id, video_id):
        select_query = """
            SELECT * FROM video WHERE user_id = ? AND video_id = ?;
            """
        self.cursor.execute(select_query, (user_id, video_id))
        return self.cursor.fetchone() is not None

    def has_user_liked(self, user_id, video_id):
        select_query = """
            SELECT reaction FROM video WHERE user_id = ? AND video_id = ?;
            """
        self.cursor.execute(select_query, (user_id, video_id))
        video = self.cursor.fetchone()
        return video is not None and 'actually_like' in video[0]


    def has_user_disliked(self, user_id, video_id):
        select_query = """
            SELECT reaction FROM video WHERE user_id = ? AND video_id = ?;
            """
        self.cursor.execute(select_query, (user_id, video_id))
        video = self.cursor.fetchone()
        return video is not None and 'dislike' in video[0]