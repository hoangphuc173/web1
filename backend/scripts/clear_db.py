import sys
import os

# Add parent directory to path to import db_manager
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from db_manager import DatabaseConnection

conn = DatabaseConnection()
cursor = conn.cursor()

cursor.execute('DELETE FROM episodes')
cursor.execute('DELETE FROM movies')
conn.commit()

print("✅ Database cleared!")

cursor.execute('SELECT COUNT(*) as total FROM movies')
print(f"Movies: {cursor.fetchone()['total']}")

cursor.execute('SELECT COUNT(*) as total FROM episodes')
print(f"Episodes: {cursor.fetchone()['total']}")

conn.close()
