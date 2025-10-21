"""
Script to re-link all existing movies with their genres
Fixes the issue where movies have genres in TEXT field but not in movie_genres table
"""
import sys
sys.path.insert(0, '.')
from db_manager import DatabaseConnection

conn = DatabaseConnection()
cursor = conn.cursor()

# Genre mapping: OPhim name -> DB name
genre_mapping = {
    'Hành Động': 'Hành động',
    'Phiêu Lưu': 'Phiêu lưu',
    'Hoạt Hình': 'Hoạt hình',
    'Hài Hước': 'Hài',
    'Hình Sự': 'Tội phạm',
    'Tài Liệu': 'Tài liệu',
    'Chính kịch': 'Chính kịch',
    'Gia Đình': 'Gia đình',
    'Giả Tượng': 'Giả tưởng',
    'Kinh Dị': 'Kinh dị',
    'Bí ẩn': 'Bí ẩn',
    'Tâm Lý': 'Chính kịch',
    'Tình Cảm': 'Lãng mạn',
    'Viễn Tưởng': 'Khoa học viễn tưởng',
    'Gây Cấn': 'Thriller',
    'Chiến Tranh': 'Chiến tranh',
    'Võ Thuật': 'Hành động',
    'Cổ Trang': 'Chính kịch',
    'Thần Thoại': 'Giả tưởng',
}

# Get all genres from DB
cursor.execute('SELECT id, name FROM genres')
db_genres = {row['name']: row['id'] for row in cursor.fetchall()}
print(f"📁 Found {len(db_genres)} genres in database")

# Get all movies
cursor.execute('SELECT id, title, genres FROM movies')
movies = cursor.fetchall()
print(f"🎬 Found {len(movies)} movies")

print("\n" + "="*70)
print("Starting genre linking...")
print("="*70)

total_links = 0
movies_updated = 0

for movie in movies:
    movie_id = movie['id']
    title = movie['title']
    genres_text = movie['genres'] or ''
    
    if not genres_text:
        continue
    
    # Parse genres from comma-separated text
    genre_names = [g.strip() for g in genres_text.split(',')]
    
    # Delete existing links for this movie
    cursor.execute('DELETE FROM movie_genres WHERE movie_id = %s', (movie_id,))
    
    movie_link_count = 0
    for genre_name in genre_names:
        # Try to map to DB genre
        db_genre_name = genre_mapping.get(genre_name, genre_name)
        genre_id = db_genres.get(db_genre_name)
        
        if genre_id:
            try:
                cursor.execute('''
                    INSERT INTO movie_genres (movie_id, genre_id) 
                    VALUES (%s, %s)
                ''', (movie_id, genre_id))
                movie_link_count += 1
                total_links += 1
            except Exception:
                # Skip duplicates
                pass
    
    if movie_link_count > 0:
        movies_updated += 1
        if movies_updated % 100 == 0:
            print(f"  ✅ Processed {movies_updated} movies ({total_links} links)...")
            conn.commit()

conn.commit()

print("\n" + "="*70)
print("✅ COMPLETED!")
print(f"  - Movies updated: {movies_updated}")
print(f"  - Total genre links created: {total_links}")
print("="*70)

# Verify
cursor.execute('SELECT COUNT(*) as count FROM movie_genres')
result = cursor.fetchone()
print(f"\n📊 Total records in movie_genres: {result['count']}")

conn.close()
