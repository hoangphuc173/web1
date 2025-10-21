"""
Direct Database Test - Verify MySQL data
"""
import sys
import os

# Add parent directory to path to import db_manager
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from db_manager import get_db

print("="*60)
print("VERIFYING MYSQL DATA")
print("="*60)

# Connect to database
db = get_db()
cursor = db.cursor()

# Test 1: Check users
print("\n1️⃣ USERS TABLE")
cursor.execute("SELECT id, name, email, role, subscription_tier FROM users LIMIT 3")
users = cursor.fetchall()
for user in users:
    if isinstance(user, dict):
        print(f"   ID: {user['id']}, Name: {user['name']}, Email: {user['email']}, Role: {user['role']}")
    else:
        print(f"   ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}")

# Test 2: Check movies
print("\n2️⃣ MOVIES TABLE")
cursor.execute("SELECT id, title, type, is_premium, release_year FROM movies LIMIT 5")
movies = cursor.fetchall()
for movie in movies:
    if isinstance(movie, dict):
        print(f"   [{movie['type'].upper()}] {movie['title']} ({movie['release_year']}) - Premium: {movie['is_premium']}")
    else:
        print(f"   [{movie[2].upper()}] {movie[1]} ({movie[4]}) - Premium: {movie[3]}")

# Test 3: Check genres
print("\n3️⃣ GENRES TABLE")
cursor.execute("SELECT id, name, slug FROM genres LIMIT 10")
genres = cursor.fetchall()
for genre in genres:
    if isinstance(genre, dict):
        print(f"   {genre['name']} ({genre['slug']})")
    else:
        print(f"   {genre[1]} ({genre[2]})")

# Test 4: Statistics
print("\n4️⃣ STATISTICS")
cursor.execute("SELECT COUNT(*) as count FROM users")
result = cursor.fetchone()
user_count = list(result.values())[0]

cursor.execute("SELECT COUNT(*) as count FROM movies")
result = cursor.fetchone()
movie_count = list(result.values())[0]

cursor.execute("SELECT COUNT(*) as count FROM genres")
result = cursor.fetchone()
genre_count = list(result.values())[0]

cursor.execute("SELECT COUNT(*) as count FROM movies WHERE type='movie'")
result = cursor.fetchone()
movie_only = list(result.values())[0]

cursor.execute("SELECT COUNT(*) as count FROM movies WHERE type='series'")
result = cursor.fetchone()
series_only = list(result.values())[0]

print(f"   Total Users: {user_count}")
print(f"   Total Movies: {movie_count}")
print(f"   - Movies only: {movie_only}")
print(f"   - Series only: {series_only}")
print(f"   Total Genres: {genre_count}")

db.close()

print("\n" + "="*60)
print("✅ MYSQL DATABASE WORKING PERFECTLY!")
print("="*60)
