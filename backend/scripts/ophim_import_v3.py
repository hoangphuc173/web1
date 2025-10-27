"""
OPhim API V3 - Import phim từ OPhim18.cc với episode data đầy đủ
Tích hợp video URL thực từ API
Auto-import: Tự động import phim mới 2 lần mỗi ngày (12:00 và 00:00)
Smart Update: Chỉ import/update phim mới dựa trên thời gian cập nhật
"""
import requests
import time
import schedule
import threading
from datetime import datetime
import sys
import os

# Add parent directory to path to import db_manager
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from db_manager import DatabaseConnection

# OPhim API Configuration
OPHIM_BASE_URL = "https://ophim1.com"
OPHIM_API_BASE = "https://ophim1.com"

class OphimImporter:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        # Genre mapping: OPhim name -> DB name
        self.genre_mapping = {
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
        
    def get_movie_list(self, page=1, limit=20, genre=None, year=None):
        """Lấy danh sách phim mới cập nhật"""
        try:
            if genre:
                url = f"{OPHIM_API_BASE}/danh-sach/{genre}"
            else:
                url = f"{OPHIM_API_BASE}/danh-sach/phim-moi-cap-nhat"
            
            params = {'page': page}
            if year:
                params['year'] = year
            
            print(f"📡 Fetching movie list (page {page}, genre={genre}, year={year})...")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # NEW API structure: data.data.items
                items = data.get('data', {}).get('items', [])
                if not items:
                    # Fallback to old structure
                    items = data.get('items', [])
                
                print(f"✅ Found {len(items)} movies")
                return items
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching movie list: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_movie_detail(self, slug):
        """Lấy chi tiết phim bao gồm episodes"""
        try:
            url = f"{OPHIM_API_BASE}/phim/{slug}"
            
            print(f"  📡 Fetching detail for: {slug}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # API có thể trả về status là 'success' hoặc True
                status = data.get('status')
                if status == 'success' or status:
                    # Return full data including episodes
                    return data
                else:
                    print(f"  ⚠️ API returned status: {status}")
                    return None
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ Error fetching movie detail: {e}")
            return None
    
    def import_movie(self, movie_data, check_update_time=False, force_update=False):
        """Import một phim vào database"""
        try:
            conn = DatabaseConnection()
            cursor = conn.cursor()
            
            # Extract movie info
            slug = movie_data.get('slug', '')
            title = movie_data.get('name', '')
            original_title = movie_data.get('origin_name', '')
            modified_time = movie_data.get('modified', {}).get('time', '')
            
            print(f"\n🎬 Processing: {title}")
            if modified_time:
                print(f"  📅 Modified: {modified_time}")
            
            # Check if movie exists
            cursor.execute('SELECT id, updated_at FROM movies WHERE title = ? OR slug = ?', (title, slug))
            existing = cursor.fetchone()
            
            if existing and not force_update:
                # If check_update_time is enabled, compare timestamps
                if check_update_time and modified_time:
                    try:
                        from datetime import datetime
                        # Parse OPhim modified time (ISO 8601 format: 2025-10-21T12:57:09.000Z)
                        # Remove milliseconds and Z, then parse
                        clean_time = modified_time.replace('.000Z', '').replace('Z', '').replace('T', ' ')
                        ophim_time = datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')
                        # Get DB updated time
                        db_time = existing['updated_at']
                        if isinstance(db_time, str):
                            db_time = datetime.strptime(db_time, '%Y-%m-%d %H:%M:%S')
                        
                        # If OPhim version is newer, update it
                        if ophim_time > db_time:
                            print(f"  🔄 Movie exists but has updates (OPhim: {ophim_time} > DB: {db_time})")
                            print(f"  ➡️ Updating movie ID: {existing['id']}")
                            # Continue to update
                        else:
                            print(f"  ✅ Movie already up-to-date (ID: {existing['id']})")
                            conn.close()
                            return {'movie_id': existing['id'], 'action': 'skipped'}
                    except Exception as e:
                        print(f"  ⚠️ Could not compare timestamps: {e}")
                        print(f"  ⚠️ Movie already exists (ID: {existing['id']})")
                        conn.close()
                        return {'movie_id': existing['id'], 'action': 'skipped'}
                else:
                    print(f"  ⚠️ Movie already exists (ID: {existing['id']})")
                    conn.close()
                    return {'movie_id': existing['id'], 'action': 'skipped'}
            
            # Get full movie details with episodes
            api_data = self.get_movie_detail(slug)
            
            if not api_data:
                print("  ❌ Could not fetch full details")
                conn.close()
                return None
            
            # Extract movie and episodes from API response
            # NEW API structure: data.item contains the movie data
            data_obj = api_data.get('data', {})
            full_movie = data_obj.get('item', api_data.get('movie', {}))
            
            # Try to get episodes from multiple possible locations
            # Priority: data.item.episodes > data.episodes > movie.episodes > root.episodes
            episodes_data = full_movie.get('episodes', [])
            if not episodes_data:
                episodes_data = data_obj.get('episodes', [])
            if not episodes_data:
                episodes_data = api_data.get('episodes', [])
            
            # Debug: Check if episodes exist
            if episodes_data:
                print(f"  📺 Found {len(episodes_data)} episode server groups")
            else:
                print("  ℹ️ No episodes found in API response")
            
            # Extract data
            content = full_movie.get('content', '')
            if content:
                content = content.replace('<p>', '').replace('</p>', '').replace('<br>', '\n')
                content = content.replace('&nbsp;', ' ').strip()[:1000]
            
            year = full_movie.get('year', 0)
            try:
                year = int(year) if year else 0
            except (ValueError, TypeError):
                year = 0
            
            # Duration
            time_str = full_movie.get('time', '')
            duration = 90
            if time_str:
                try:
                    duration = int(''.join(filter(str.isdigit, time_str)))
                except (ValueError, TypeError):
                    duration = 90
            
            # Type
            movie_type = full_movie.get('type', 'single')
            if movie_type == 'series' or movie_type == 'hoathinh':
                content_type = 'series'
            else:
                content_type = 'movie'
            
            # Country
            country_list = full_movie.get('country', [])
            country = country_list[0].get('name') if country_list and len(country_list) > 0 else 'Unknown'
            
            # Director & Cast
            director_list = full_movie.get('director', [])
            if isinstance(director_list, list) and len(director_list) > 0:
                if isinstance(director_list[0], dict):
                    director = ', '.join([d.get('name', '') for d in director_list])
                else:
                    director = ', '.join([str(d) for d in director_list if d])
            else:
                director = ''
            
            actor_list = full_movie.get('actor', [])
            if isinstance(actor_list, list) and len(actor_list) > 0:
                if isinstance(actor_list[0], dict):
                    cast = ', '.join([a.get('name', '') for a in actor_list])
                else:
                    cast = ', '.join([str(a) for a in actor_list if a])
            else:
                cast = ''
            
            # Genres
            category_list = full_movie.get('category', [])
            genres = ', '.join([cat.get('name', '') for cat in category_list])
            
            # Rating
            tmdb = full_movie.get('tmdb', {})
            imdb_rating = tmdb.get('vote_average', 0)
            if imdb_rating:
                try:
                    imdb_rating = float(imdb_rating)
                except (ValueError, TypeError):
                    imdb_rating = 0.0
            
            # Images
            poster_url = full_movie.get('poster_url', '')
            thumb_url = full_movie.get('thumb_url', '')
            
            # Trailer
            trailer_url = full_movie.get('trailer_url', '')
            
            # **QUAN TRỌNG: Video URL từ episodes** (đã extract ở trên)
            video_url = f"{OPHIM_API_BASE}/phim/{slug}"  # Default to page URL
            
            # Try to get actual video URL from first episode
            if episodes_data and len(episodes_data) > 0:
                server_data = episodes_data[0].get('server_data', [])
                if server_data and len(server_data) > 0:
                    first_episode = server_data[0]
                    # Get embed link
                    link_embed = first_episode.get('link_embed', '')
                    link_m3u8 = first_episode.get('link_m3u8', '')
                    
                    if link_m3u8:
                        video_url = link_m3u8
                        print(f"  📹 Got M3U8 URL: {link_m3u8[:50]}...")
                    elif link_embed:
                        video_url = link_embed
                        print(f"  📹 Got Embed URL: {link_embed[:50]}...")
            
            # Premium status (random for demo)
            is_premium = 0 
            
            # Check if this is an update or new insert
            if existing:
                # UPDATE existing movie
                # Use Ophim's modified time if available, otherwise use current timestamp
                if modified_time:
                    try:
                        from datetime import datetime
                        clean_time = modified_time.replace('.000Z', '').replace('Z', '').replace('T', ' ')
                        ophim_datetime = datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')
                        updated_at_value = ophim_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        updated_at_value = None  # Use CURRENT_TIMESTAMP
                else:
                    updated_at_value = None
                
                if updated_at_value:
                    cursor.execute('''
                        UPDATE movies SET
                            original_title = ?, description = ?, release_year = ?, duration = ?,
                            country = ?, language = ?, director = ?, cast = ?, genres = ?, imdb_rating = ?,
                            poster_url = ?, backdrop_url = ?, trailer_url = ?, video_url = ?,
                            type = ?, is_premium = ?, status = ?, updated_at = ?
                        WHERE id = ?
                    ''', (
                        original_title, content, year, duration,
                        country, 'Vietsub', director, cast, genres, imdb_rating,
                        poster_url, thumb_url, trailer_url, video_url,
                        content_type, is_premium, 'active', updated_at_value, existing['id']
                    ))
                else:
                    cursor.execute('''
                        UPDATE movies SET
                            original_title = ?, description = ?, release_year = ?, duration = ?,
                            country = ?, language = ?, director = ?, cast = ?, genres = ?, imdb_rating = ?,
                            poster_url = ?, backdrop_url = ?, trailer_url = ?, video_url = ?,
                            type = ?, is_premium = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        original_title, content, year, duration,
                        country, 'Vietsub', director, cast, genres, imdb_rating,
                        poster_url, thumb_url, trailer_url, video_url,
                        content_type, is_premium, 'active', existing['id']
                    ))
                movie_id = existing['id']
                action = 'updated'
                print(f"  ✅ Updated movie ID: {movie_id}")
            else:
                # INSERT new movie
                # Use Ophim's modified time for both created_at and updated_at
                if modified_time:
                    try:
                        from datetime import datetime
                        clean_time = modified_time.replace('.000Z', '').replace('Z', '').replace('T', ' ')
                        ophim_datetime = datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')
                        timestamp_value = ophim_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        timestamp_value = None
                else:
                    timestamp_value = None
                
                if timestamp_value:
                    cursor.execute('''
                        INSERT INTO movies (
                            title, original_title, slug, description, release_year, duration,
                            country, language, director, cast, genres, imdb_rating,
                            poster_url, backdrop_url, trailer_url, video_url, 
                            type, is_premium, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        title, original_title, slug, content, year, duration,
                        country, 'Vietsub', director, cast, genres, imdb_rating,
                        poster_url, thumb_url, trailer_url, video_url,
                        content_type, is_premium, 'active', timestamp_value, timestamp_value
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO movies (
                            title, original_title, slug, description, release_year, duration,
                            country, language, director, cast, genres, imdb_rating,
                            poster_url, backdrop_url, trailer_url, video_url, 
                            type, is_premium, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        title, original_title, slug, content, year, duration,
                        country, 'Vietsub', director, cast, genres, imdb_rating,
                        poster_url, thumb_url, trailer_url, video_url,
                        content_type, is_premium, 'active'
                    ))
                
                movie_id = cursor.lastrowid
                action = 'inserted'
                print(f"  ✅ Inserted movie ID: {movie_id}")
            
            # Insert genres into movie_genres table
            if category_list and movie_id:
                # First, delete existing genre links for this movie
                cursor.execute('DELETE FROM movie_genres WHERE movie_id = %s', (movie_id,))
                
                # Get all genre IDs from database
                cursor.execute('SELECT id, name FROM genres')
                db_genres = {row['name']: row['id'] for row in cursor.fetchall()}
                
                # Insert new genre links
                genre_count = 0
                for cat in category_list:
                    ophim_genre_name = cat.get('name', '')
                    # Try to map OPhim genre to DB genre
                    db_genre_name = self.genre_mapping.get(ophim_genre_name, ophim_genre_name)
                    
                    # Find matching genre ID
                    genre_id = db_genres.get(db_genre_name)
                    if genre_id:
                        try:
                            cursor.execute('''
                                INSERT INTO movie_genres (movie_id, genre_id) 
                                VALUES (%s, %s)
                            ''', (movie_id, genre_id))
                            genre_count += 1
                        except Exception:
                            # Skip duplicates
                            pass
                
                if genre_count > 0:
                    print(f"  📁 Linked {genre_count} genres")
            
            # Insert episodes if series
            if content_type == 'series':
                if not episodes_data:
                    print("  ⚠️ Series but no episodes data found!")
                else:
                    print(f"  📺 Processing episodes for series (type: {content_type})")
            
            if content_type == 'series' and episodes_data:
                episode_count = 0
                new_episodes = 0
                
                for server_group in episodes_data:
                    server_name = server_group.get('server_name', 'Server 1')
                    server_data = server_group.get('server_data', [])
                    print(f"  📡 Server: {server_name} - {len(server_data)} episodes")
                    
                    for ep_data in server_data:
                        ep_name_raw = ep_data.get('name', '')
                        
                        # Normalize episode name to just number for consistency
                        # API returns "Tập 1", "Tập 2", etc. but we store just "1", "2"
                        ep_name = ep_name_raw
                        if 'Tập' in ep_name_raw or 'tập' in ep_name_raw:
                            # Extract number from "Tập 17" -> "17"
                            import re
                            match = re.search(r'(\d+)', ep_name_raw)
                            if match:
                                ep_name = match.group(1)
                        
                        link_embed = ep_data.get('link_embed', '')
                        link_m3u8 = ep_data.get('link_m3u8', '')
                        
                        # Use m3u8 if available, else embed
                        episode_url = link_m3u8 if link_m3u8 else link_embed
                        
                        if episode_url:
                            episode_count += 1
                            
                            # Check if episode already exists (by name and server)
                            cursor.execute('''
                                SELECT id FROM episodes 
                                WHERE movie_id = %s AND episode_name = %s AND server_name = %s
                            ''', (movie_id, ep_name, server_name))
                            
                            existing_episode = cursor.fetchone()
                            
                            if not existing_episode:
                                # Insert new episode only
                                cursor.execute('''
                                    INSERT INTO episodes (
                                        movie_id, episode_number, episode_name, video_url, server_name
                                    ) VALUES (%s, %s, %s, %s, %s)
                                ''', (movie_id, episode_count, ep_name, episode_url, server_name))
                                new_episodes += 1
                
                if new_episodes > 0:
                    print(f"  ✅ Added {new_episodes} new episodes (Total: {episode_count} episodes)")
                elif episode_count > 0:
                    print(f"  ℹ️ All {episode_count} episodes already exist")
            
            conn.commit()
            conn.close()
            
            return {'movie_id': movie_id, 'action': action}
            
        except Exception as e:
            print(f"  ❌ Error importing movie: {e}")
            import traceback
            traceback.print_exc()
            return None

    def import_batch(self, num_pages=5, genre=None, year=None, check_update_time=False):
        """Import nhiều trang phim với smart update
        
        Args:
            num_pages: Số trang để import
            genre: Filter theo thể loại
            year: Filter theo năm
            check_update_time: Smart update - chỉ import phim mới/cập nhật, tự động dừng khi gặp phim cũ
        """
        print("=" * 70)
        print("🎬 OPHIM IMPORTER V3 - Full Episode Support")
        if check_update_time:
            print("🔄 Smart Update: Auto-stop when reaching old movies")
        print("=" * 70)
        
        total_imported = 0
        total_updated = 0
        total_skipped = 0
        consecutive_skipped = 0
        SKIP_THRESHOLD = 3  # Dừng khi 3 phim liên tiếp đã up-to-date
        
        for page in range(1, num_pages + 1):
            print(f"\n📄 Processing page {page}/{num_pages}")
            print("-" * 70)
            
            movies = self.get_movie_list(page=page, genre=genre, year=year)
            
            if not movies:
                print(f"⚠️ No movies found on page {page}, stopping...")
                break
            
            for idx, movie in enumerate(movies, 1):
                print(f"\n[{idx}/{len(movies)}]", end=" ")
                result = self.import_movie(movie, check_update_time=check_update_time)
                
                # Handle result
                if result and isinstance(result, dict):
                    action = result.get('action', 'unknown')
                    
                    if action == 'inserted':
                        total_imported += 1
                        consecutive_skipped = 0
                    elif action == 'updated':
                        total_updated += 1
                        consecutive_skipped = 0
                    elif action == 'skipped':
                        total_skipped += 1
                        consecutive_skipped += 1
                else:
                    # Null result = error
                    total_skipped += 1
                    consecutive_skipped += 1
                
                # Early stop logic - chỉ khi check_update_time = True
                if check_update_time and consecutive_skipped >= SKIP_THRESHOLD:
                    print(f"\n⚡ Early stop: {consecutive_skipped} consecutive movies already up-to-date")
                    print("   All newer movies imported. Stopping here to save time.")
                    break
                
                # Rate limiting - giảm xuống để import nhanh hơn
                time.sleep(0.2)
            
            # Break outer loop if early stop triggered
            if check_update_time and consecutive_skipped >= SKIP_THRESHOLD:
                break
            
            print(f"\n✅ Page {page} completed")
            time.sleep(0.5)
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 Import Summary:")
        print(f"   ✅ New movies: {total_imported}")
        print(f"   🔄 Updated: {total_updated}")
        print(f"   ⏩ Skipped: {total_skipped}")
        print("=" * 70)
        
        return total_imported + total_updated


class AutoImporter:
    """Tự động import phim theo lịch"""
    
    def __init__(self):
        self.importer = OphimImporter()
        self.is_running = False
        
    def daily_import_job(self):
        """Job import hằng ngày"""
        try:
            print("\n" + "=" * 70)
            print(f"⏰ Auto Import Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)
            
            # Import 3 pages of new movies with smart update
            total = self.importer.import_batch(num_pages=3, year=None, check_update_time=True)
            
            print("\n" + "=" * 70)
            print(f"✅ Auto Import Completed: {total} movies imported/updated")
            print("🕐 Next run: 12:00 (noon) or 00:00 (midnight)")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Auto import error: {e}")
            import traceback
            traceback.print_exc()
    
    def continuous_import_job(self):
        """Job import liên tục (real-time) - chạy mỗi vài phút"""
        try:
            print("\n" + "=" * 70)
            print(f"🔄 Continuous Import at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)
            
            # Import 1 page (20 phim mới nhất) với smart update
            # Chỉ update phim có thời gian modified mới hơn DB
            total = self.importer.import_batch(num_pages=1, year=None, check_update_time=True)
            
            print(f"✅ Continuous Import Done: {total} movies checked")
            
        except Exception as e:
            print(f"❌ Continuous import error: {e}")
            import traceback
            traceback.print_exc()
    
    def start_scheduler(self, continuous=False, interval_minutes=10):
        """Bắt đầu scheduler (chạy trong background thread)
        
        Args:
            continuous: Nếu True, chạy continuous mode (liên tục mỗi X phút)
            interval_minutes: Khoảng thời gian giữa các lần import (phút)
        """
        def run_schedule():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        if continuous:
            # Continuous mode: Import mỗi X phút
            schedule.every(interval_minutes).minutes.do(self.continuous_import_job)
            schedule_info = f"Every {interval_minutes} minutes (Real-time mode)"
        else:
            # Normal mode: Import 2 lần/ngày
            schedule.every().day.at("12:00").do(self.daily_import_job)
            schedule.every().day.at("00:00").do(self.daily_import_job)
            schedule_info = "Daily at 12:00 (noon) and 00:00 (midnight)"
        
        self.is_running = True
        scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        scheduler_thread.start()
        
        print("\n" + "=" * 70)
        print("🤖 Auto Import Scheduler Started")
        print(f"📅 Schedule: {schedule_info}")
        print("🔄 Running in background...")
        print("=" * 70)
        
        return scheduler_thread
    
    def stop_scheduler(self):
        """Dừng scheduler"""
        self.is_running = False
        schedule.clear()
        print("🛑 Scheduler stopped")
    
    def run_now(self):
        """Chạy import ngay lập tức (không đợi đến 23:59)"""
        print("🚀 Running import immediately...")
        self.daily_import_job()


def main():
    """Main function"""
    import argparse
    parser = argparse.ArgumentParser(description='OPhim Importer V3')
    parser.add_argument('--slug', type=str, help='Import phim theo slug')
    parser.add_argument('--genre', type=str, help='Import theo thể loại (genre)')
    parser.add_argument('--year', type=int, help='Chỉ import phim mới theo năm')
    parser.add_argument('--pages', type=int, default=3, help='Số trang import')
    parser.add_argument('--auto', action='store_true', help='Bật chế độ tự động import hằng ngày lúc 12:00 và 00:00')
    parser.add_argument('--continuous', action='store_true', help='Chế độ liên tục - import mỗi X phút (real-time)')
    parser.add_argument('--interval', type=int, default=10, help='Khoảng thời gian giữa các lần import (phút) - dùng với --continuous')
    parser.add_argument('--run-now', action='store_true', help='Chạy auto-import ngay lập tức')
    parser.add_argument('--check-update', action='store_true', help='Chỉ import phim mới/cập nhật (so sánh thời gian)')
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🚀 Starting OPhim Import")
    if args.check_update:
        print("🔄 Smart Update Mode: Only new/updated movies")
    print("=" * 70)
    
    # Auto import mode
    if args.auto or args.continuous or args.run_now:
        auto_importer = AutoImporter()
        
        if args.run_now:
            # Run immediately
            auto_importer.run_now()
        else:
            # Start scheduler
            if args.continuous:
                print(f"\n🔄 Continuous Mode: Import every {args.interval} minutes")
                auto_importer.start_scheduler(continuous=True, interval_minutes=args.interval)
            else:
                print("\n📅 Scheduled Mode: Import at 12:00 and 00:00 daily")
                auto_importer.start_scheduler(continuous=False)
            
            # Keep main thread alive
            try:
                print("\n💡 Press Ctrl+C to stop the scheduler\n")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping scheduler...")
                auto_importer.stop_scheduler()
                print("👋 Goodbye!")
        
        return
    
    # Manual import mode
    importer = OphimImporter()
    
    if args.slug:
        print(f"🔎 Importing phim theo slug: {args.slug}")
        movie = importer.get_movie_detail(args.slug)
        if movie:
            importer.import_movie(movie, check_update_time=args.check_update)
        else:
            print(f"❌ Không tìm thấy phim với slug: {args.slug}")
    else:
        importer.import_batch(num_pages=args.pages, genre=args.genre, year=args.year, check_update_time=args.check_update)
    
    print("\n✅ All done!")


if __name__ == '__main__':
    main()
