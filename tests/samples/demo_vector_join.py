import sqlite3
import json

conn = sqlite3.connect('tests/output/app2.db')
conn.enable_load_extension(True)
import sqlite_vec
sqlite_vec.load(conn)

cursor = conn.cursor()

# Query demonstrating how Vector RowID links to Original Table Row ID!
# 1. We query etl_semantic_vectors (which only has rowid and embedding)
# 2. We join on etl_semantic_index using id = rowid
# 3. We extract the original table primary key ('id') from metadata_json!
# 4. We join the original canonical 'companies' table using that extracted ID!
sql = """
SELECT 
    v.id as vector_id,
    v.source_row_id as original_company_id,
    c.name as original_company_name,
    c._record_hash
FROM etl_semantic_vectors v
JOIN companies c ON c.id = v.source_row_id
LIMIT 3;
"""

print("--- Vector to Source Row Lineage Query ---")
cursor.execute(sql)
for row in cursor.fetchall():
    print(f"Vector ID: {row[0]}")
    print(f"Original Company ID: {row[1]}")
    print(f"Original Company Name: {row[2]}")
    print(f"Record Hash: {row[3]}")
    print("-" * 50)

conn.close()
