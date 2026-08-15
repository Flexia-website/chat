"""
One-off migration: copies all data from the old flexia_chat.db (SQLite)
into the PostgreSQL database pointed to by DATABASE_URL.

Run this ONCE, before (or right after) you switch DATABASE_URL over —
app.py's init_db() creates the Postgres tables automatically on startup,
so it's safe to start the app first and run this migration after.

Usage:
    DATABASE_URL=postgresql://user:pass@host:port/dbname python migrate_to_postgres.py
    # or, to point at a specific sqlite file:
    python migrate_to_postgres.py /path/to/flexia_chat.db

Note: this only migrates database rows. If you also want the actual
uploaded images to survive, copy the local `uploads/` folder to the new
server yourself — Render's free plan does not persist disk across deploys.
"""
import os
import sys
import sqlite3
import psycopg2
import psycopg2.extras

SQLITE_PATH = sys.argv[1] if len(sys.argv) > 1 else 'flexia_chat.db'
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print('❌ Set DATABASE_URL to your Postgres connection string first.')
    sys.exit(1)

if not os.path.exists(SQLITE_PATH):
    print(f'❌ SQLite file not found: {SQLITE_PATH}')
    sys.exit(1)

# Tables in FK-safe order (users before messages/uploaded_files)
TABLES = [
    ('users', ['id', 'device_id', 'username', 'created_at', 'last_active']),
    ('messages', ['id', 'device_id', 'sender', 'message', 'type', 'is_admin',
                  'is_auto_reply', 'timestamp', 'expires_at']),
    ('uploaded_files', ['id', 'device_id', 'filename', 'filepath', 'uploaded_at', 'expires_at']),
    ('auto_replies', ['id', 'reply_text', 'created_at']),
    ('settings', ['key', 'value']),
    ('push_subscriptions', ['id', 'device_id', 'endpoint', 'p256dh', 'auth', 'created_at']),
]

sconn = sqlite3.connect(SQLITE_PATH)
sconn.row_factory = sqlite3.Row
pconn = psycopg2.connect(DATABASE_URL)
pcur = pconn.cursor()

print(f'📦 Migrating from {SQLITE_PATH} -> Postgres')

for table, columns in TABLES:
    try:
        rows = sconn.execute(f'SELECT {", ".join(columns)} FROM {table}').fetchall()
    except sqlite3.OperationalError as e:
        print(f'  ⏭  Skipping {table} (not found in sqlite: {e})')
        continue

    if not rows:
        print(f'  ⏭  {table}: no rows')
        continue

    placeholders = ', '.join(['%s'] * len(columns))
    col_list = ', '.join(columns)
    conflict_col = 'key' if table == 'settings' else 'id'
    insert_sql = f'''INSERT INTO {table} ({col_list}) VALUES ({placeholders})
                      ON CONFLICT ({conflict_col}) DO NOTHING'''

    count = 0
    for row in rows:
        values = [row[col] for col in columns]
        # SQLite stores booleans as 0/1 ints; cast for the boolean columns
        if table == 'messages':
            is_admin_idx = columns.index('is_admin')
            is_auto_reply_idx = columns.index('is_auto_reply')
            values[is_admin_idx] = bool(values[is_admin_idx])
            values[is_auto_reply_idx] = bool(values[is_auto_reply_idx])
        pcur.execute(insert_sql, values)
        count += 1

    pconn.commit()
    print(f'  ✅ {table}: {count} rows migrated')

    # Reset the SERIAL sequence so future inserts don't collide with migrated IDs
    if 'id' in columns:
        pcur.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
        )
        pconn.commit()

sconn.close()
pcur.close()
pconn.close()

print('🎉 Migration complete')
