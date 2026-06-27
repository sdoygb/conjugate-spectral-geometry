import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'chroma_db', 'chroma.sqlite3')
print(f"数据库路径: {db_path}")
print(f"文件存在: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print('\n=== 数据库表 ===')
for t in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{t[0]}"')
        count = cursor.fetchone()[0]
        print(f'  {t[0]}: {count} 行')
    except Exception as e:
        print(f'  {t[0]}: 查询失败 - {e}')

# collections 表
print('\n=== collections 表 ===')
try:
    cursor.execute('SELECT id, name, metadata, dimension FROM collections')
    for row in cursor.fetchall():
        meta_str = str(row[2])[:200] if row[2] else None
        print(f'  id={row[0]}, name={row[1]}, dim={row[3]}, metadata={meta_str}')
except Exception as e:
    print(f'  查询失败: {e}')

# segments 表 - 查看所有集合的分段数
print('\n=== segments 表 ===')
try:
    cursor.execute('SELECT id, collection_id, metadata FROM segments')
    rows = cursor.fetchall()
    print(f'  共 {len(rows)} 条记录')
    for row in rows:
        print(f'  id={row[0]}, collection_id={row[1]}, metadata={str(row[2])[:100]}')
except Exception as e:
    print(f'  查询失败: {e}')

conn.close()