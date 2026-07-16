import sqlite3

# MUST connect to the output database, NOT the immutable source database
conn = sqlite3.connect('tests/output/app4.db')

# Enable SQLite extension loading to view vec0 virtual tables
conn.enable_load_extension(True)
import sqlite_vec
sqlite_vec.load(conn)

cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print('Tables in Output DB:', tables)

for t in tables:  # Removed slicing so ALL tables are inspected
    quoted_t = f'"{t}"'
    cursor.execute(f'PRAGMA table_info({quoted_t})')
    cols = cursor.fetchall()
    print(f'{t} columns:', [c[1] for c in cols])
    cursor.execute(f'SELECT COUNT(*) FROM {quoted_t}')
    print(f'{t} row count:', cursor.fetchone()[0])
conn.close()
