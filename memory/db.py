import psycopg2
from psycopg2.extras import RealDictCursor
import json
from config import settings

class DatabaseManager:
    """Handles PostgreSQL connection and operations for MeetingMind AI."""
    
    def __init__(self):
        self.url = settings.DATABASE_URL
        self._init_db()

    def get_connection(self):
        """Get a fresh database connection."""
        return psycopg2.connect(self.url, cursor_factory=RealDictCursor)

    def _init_db(self):
        """Create the meetings table if it doesn't exist."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS meetings (
                            meeting_id VARCHAR(255) PRIMARY KEY,
                            org_id VARCHAR(255),
                            pipeline_status VARCHAR(50),
                            data JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                conn.commit()
            print("[INFO] PostgreSQL meetings table initialized.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize PostgreSQL table: {e}")

    def save_meeting(self, meeting_id: str, org_id: str, pipeline_status: str, data: dict):
        """Insert or update a meeting record in PostgreSQL."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO meetings (meeting_id, org_id, pipeline_status, data)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (meeting_id) 
                        DO UPDATE SET 
                            pipeline_status = EXCLUDED.pipeline_status,
                            data = EXCLUDED.data;
                    """, (meeting_id, org_id, pipeline_status, json.dumps(data)))
                conn.commit()
        except Exception as e:
            print(f"[ERROR] DB Save failed for {meeting_id}: {e}")

    def list_meetings(self, org_id: str):
        """Retrieve a list of all meetings for an organization."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Filter by org_id if required, currently returning all for demo
                    cur.execute("SELECT meeting_id, org_id, pipeline_status, data FROM meetings ORDER BY created_at DESC;")
                    rows = cur.fetchall()
                    return rows
        except Exception as e:
            print(f"[ERROR] DB List failed: {e}")
            return []

    def get_meeting(self, meeting_id: str):
        """Retrieve a specific meeting's full JSON data."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM meetings WHERE meeting_id = %s;", (meeting_id,))
                    row = cur.fetchone()
                    if row:
                        return row["data"]
            return None
        except Exception as e:
            print(f"[ERROR] DB Get failed for {meeting_id}: {e}")
            return None

# Global instance
db_manager = DatabaseManager()
