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
    cursor.execute(f'PRAGMA table_info({t})')
    cols = cursor.fetchall()
    print(f'{t} columns:', [c[1] for c in cols])
    cursor.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'{t} row count:', cursor.fetchone()[0])
conn.close()
