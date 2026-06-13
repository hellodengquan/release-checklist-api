import sqlite3
import os

db_path = "./release_checklist.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(releases)")
        columns = [col[1] for col in cursor.fetchall()]

        if "blocker_count" not in columns:
            print("Adding blocker_count column to releases table...")
            cursor.execute("ALTER TABLE releases ADD COLUMN blocker_count INTEGER NOT NULL DEFAULT 0")

        print("Initializing blocker_count for existing releases...")
        cursor.execute("SELECT id FROM releases")
        release_ids = [row[0] for row in cursor.fetchall()]

        for release_id in release_ids:
            cursor.execute("""
                SELECT COUNT(*) FROM check_items
                WHERE release_id = ?
                AND is_blocking = 1
                AND status NOT IN ('passed', 'skipped')
            """, (release_id,))
            count = cursor.fetchone()[0]
            cursor.execute(
                "UPDATE releases SET blocker_count = ? WHERE id = ?",
                (count, release_id)
            )
            print(f"  Release {release_id}: {count} blockers")

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print("Database not found, no migration needed.")
