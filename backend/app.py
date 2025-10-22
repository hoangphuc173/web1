"""
Flask Backend Server - MySQL Database
Provides REST API for streaming movie platform
"""
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from dotenv import load_dotenv
import re
import unicodedata
import os

# Environment will be loaded by db_manager; no need to load here

from db_manager import DatabaseConnection
from flask_caching import Cache
from functools import wraps
from pymysql import IntegrityError
from datetime import timedelta

# Load environment variables FIRST
load_dotenv()

# ============================================================================
# Smart Search Helper - Vietnamese Movie Search Optimization
# ============================================================================

class SmartSearchHelper:
    """Helper class for intelligent movie search"""
    
    @staticmethod
    def normalize_vietnamese(text):
        """Normalize Vietnamese text: lowercase + trim spaces"""
        if not text:
            return ''
        text = text.lower().strip()
        return re.sub(r'\s+', ' ', text)
    
    @staticmethod
    def remove_diacritics(text):
        """Remove Vietnamese diacritics for fuzzy matching"""
        if not text:
            return ''
        nfd = unicodedata.normalize('NFD', text)
        without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
        return without_accents.replace('đ', 'd').replace('Đ', 'D')
    
    @staticmethod
    def build_smart_search_query(user_query):
        """Build optimized MySQL FULLTEXT search query with wildcards"""
        if not user_query or not user_query.strip():
            return None, None
        
        normalized = SmartSearchHelper.normalize_vietnamese(user_query)
        has_operators = any(op in user_query for op in ['*', '+', '-', '"', '(', ')'])
        
        if has_operators:
            return user_query, 'IN BOOLEAN MODE'
        
        words = normalized.split()
        if not words:
            return user_query, 'IN BOOLEAN MODE'
        
        fuzzy_terms = []
        for word in words:
            word_len = len(word)
            if word_len <= 2:
                fuzzy_terms.append(f'+{word}')  # Short: exact match
            elif word_len <= 5:
                fuzzy_terms.append(f'{word}*')  # Medium: suffix wildcard
            else:
                fuzzy_terms.append(f'{word}*')  # Long: flexible
        
        return ' '.join(fuzzy_terms), 'IN BOOLEAN MODE'
    
    @staticmethod
    def calculate_relevance_boost(movie, query_words):
        """Calculate custom relevance score boost for better ranking"""
        if not movie or not query_words:
            return 0.0
        
        score = 0.0
        title_vn = movie.get('title', '').strip().lower()
        title_en = movie.get('original_title', '').strip().lower()
        title_vn_no_accent = SmartSearchHelper.remove_diacritics(title_vn)
        
        query_str = ' '.join(query_words).lower()
        query_str_no_accent = SmartSearchHelper.remove_diacritics(query_str)
        
        # Priority 1: Title STARTS with full query (+1000)
        if (title_vn.startswith(query_str) or 
            title_vn_no_accent.startswith(query_str_no_accent) or
            title_en.startswith(query_str)):
            score += 1000.0
        # Priority 2: Title STARTS with first word (+500)
        elif query_words:
            first_word = query_words[0].lower()
            first_word_no_accent = SmartSearchHelper.remove_diacritics(first_word)
            if (title_vn.startswith(first_word) or 
                title_vn_no_accent.startswith(first_word_no_accent) or
                title_en.startswith(first_word)):
                score += 500.0
            # Priority 3: Title STARTS with other word (+300)
            else:
                for word in query_words[1:]:
                    word_norm = word.lower()
                    word_no_accent = SmartSearchHelper.remove_diacritics(word)
                    if (title_vn.startswith(word_norm) or 
                        title_vn_no_accent.startswith(word_no_accent) or
                        title_en.startswith(word_norm)):
                        score += 300.0
                        break
        
        # Exact match (+200)
        if (query_str == title_vn or query_str_no_accent == title_vn_no_accent or query_str == title_en):
            score += 200.0
        
        # All words present
        words_in_title = sum(1 for word in query_words 
                           if (word.lower() in title_vn or 
                               SmartSearchHelper.remove_diacritics(word).lower() in title_vn_no_accent or 
                               word.lower() in title_en))
        score += 100.0 if words_in_title == len(query_words) else words_in_title * 30.0
        
        # Position bonus
        for word in query_words:
            positions = [p for p in [
                title_vn.find(word.lower()),
                title_vn_no_accent.find(SmartSearchHelper.remove_diacritics(word).lower()),
                title_en.find(word.lower())
            ] if p >= 0]
            if positions:
                pos = min(positions)
                score += 50.0 if pos == 0 else (30.0 if pos <= 5 else (15.0 if pos <= 10 else 0))
        
        # Rating boost
        rating = float(movie.get('imdb_rating', 0) or 0)
        if rating >= 7.0:
            score += rating * 5.0
        
        # Views boost
        views = int(movie.get('views', 0) or 0)
        score += min(views / 1000.0, 50.0)
        
        # Recent release boost
        year = int(movie.get('release_year', 0) or 0)
        if year >= 2020:
            score += (year - 2019) * 3.0
        
        return score
    
    @staticmethod
    def highlight_keywords(text, keywords):
        """Highlight keywords in text with <mark> tags"""
        if not text or not keywords:
            return text
        result = text
        for keyword in keywords:
            if len(keyword) >= 2:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                result = pattern.sub(lambda m: f'<mark>{m.group()}</mark>', result)
        return result

    @staticmethod
    def compute_prefix_flags(movie, query_words):
        """Compute strict prefix priority flags for sorting.
        Priority order: full query prefix > first word prefix > any other word prefix.
        Case- and accent-insensitive, supports Vietnamese.
        Returns tuple: (full_prefix:int, first_prefix:int, other_prefix:int, matched_count:int)
        """
        try:
            title_vn = (movie.get('title') or '').strip()
            title_en = (movie.get('original_title') or '').strip()
        except AttributeError:
            title_vn = str(movie.get('title', '')).strip()
            title_en = str(movie.get('original_title', '')).strip()

        t_vn_l = title_vn.lower()
        t_vn_na = SmartSearchHelper.remove_diacritics(t_vn_l)
        t_en_l = title_en.lower()

        q_words = [w.lower() for w in (query_words or []) if w]
        q_words_na = [SmartSearchHelper.remove_diacritics(w) for w in q_words]

        full_q = ' '.join(q_words)
        full_q_na = ' '.join(q_words_na)

        full_prefix = 1 if (t_vn_l.startswith(full_q) or t_vn_na.startswith(full_q_na) or t_en_l.startswith(full_q)) and full_q else 0

        first_prefix = 0
        other_prefix = 0
        if not full_prefix and q_words:
            fw = q_words[0]
            fw_na = q_words_na[0]
            if t_vn_l.startswith(fw) or t_vn_na.startswith(fw_na) or t_en_l.startswith(fw):
                first_prefix = 1
            else:
                for w, wna in zip(q_words[1:], q_words_na[1:]):
                    if t_vn_l.startswith(w) or t_vn_na.startswith(wna) or t_en_l.startswith(w):
                        other_prefix = 1
                        break

        # Count how many query words appear anywhere (diacritics-insensitive)
        matched_count = 0
        for w, wna in zip(q_words, q_words_na):
            if (w in t_vn_l) or (wna in t_vn_na) or (w in t_en_l):
                matched_count += 1

        return (full_prefix, first_prefix, other_prefix, matched_count)

# Create singleton instance
smart_search = SmartSearchHelper()

# ============================================================================
# Flask App Configuration
# ============================================================================

# App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Session Configuration
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Cache Configuration
app.config['CACHE_TYPE'] = 'SimpleCache'  # In-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
cache = Cache(app)

# ============================================================================
# Static paths (absolute) for Linux compatibility
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PUBLIC_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend', 'public'))
PAGES_DIR = os.path.join(FRONTEND_PUBLIC_DIR, 'pages')
CSS_DIR = os.path.join(FRONTEND_PUBLIC_DIR, 'css')
JS_DIR = os.path.join(FRONTEND_PUBLIC_DIR, 'js')

def get_db():
    """Get database connection using db_manager"""
    return DatabaseConnection()

def hash_password(password):
    """Hash password using Werkzeug's secure hash"""
    return generate_password_hash(password)

def verify_password(password, password_hash):
    """Verify password against Werkzeug's hash"""
    return check_password_hash(password_hash, password)

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    """Initialize database with streaming platform tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # MySQL syntax only
    auto_increment = "INT AUTO_INCREMENT PRIMARY KEY"
    timestamp_update = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    tinyint = "TINYINT(1)"
    
    # ===== USERS TABLE (Enhanced with roles and subscription) =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id {auto_increment},
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'free',
            subscription_tier VARCHAR(50) DEFAULT 'free',
            subscription_expires TIMESTAMP NULL,
            profile_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at {timestamp_update}
        )
    ''')
    
    # ===== MOVIES TABLE =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS movies (
            id {auto_increment},
            title VARCHAR(500) NOT NULL,
            original_title VARCHAR(500),
            description TEXT,
            release_year INT,
            duration INT,
            country VARCHAR(100),
            language VARCHAR(100),
            director VARCHAR(255),
            cast TEXT,
            genres TEXT,
            imdb_rating DECIMAL(3,1),
            poster_url TEXT,
            backdrop_url TEXT,
            trailer_url TEXT,
            video_url TEXT,
            video_quality VARCHAR(50) DEFAULT '1080p',
            type VARCHAR(50) DEFAULT 'movie',
            is_premium {tinyint} DEFAULT 0,
            views INT DEFAULT 0,
            likes INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'active',
            slug VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at {timestamp_update}
        )
    ''')
    
    # Add type column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE movies ADD COLUMN type VARCHAR(50) DEFAULT 'movie'")
    except Exception:
        pass  # Column already exists
    
    # Add slug column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE movies ADD COLUMN slug VARCHAR(500)")
    except Exception:
        pass  # Column already exists
    
    # ===== GENRES TABLE =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS genres (
            id {auto_increment},
            name VARCHAR(255) NOT NULL UNIQUE,
            slug VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== MOVIE_GENRES (Many-to-Many) =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movie_genres (
            movie_id INT,
            genre_id INT,
            PRIMARY KEY (movie_id, genre_id),
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres (id) ON DELETE CASCADE
        )
    ''')
    
    # ===== WATCH HISTORY =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS watch_history (
            id {auto_increment},
            user_id INT NOT NULL,
            movie_id INT NOT NULL,
            progress INT DEFAULT 0,
            completed {tinyint} DEFAULT 0,
            last_watched {timestamp_update},
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
        )
    ''')
    
    # ===== FAVORITES =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS favorites (
            id {auto_increment},
            user_id INT NOT NULL,
            movie_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, movie_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
        )
    ''')
    
    # ===== REVIEWS =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS reviews (
            id {auto_increment},
            user_id INT NOT NULL,
            movie_id INT NOT NULL,
            rating INT CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            likes INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at {timestamp_update},
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
        )
    ''')
    
    # ===== COMMENTS =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS comments (
            id {auto_increment},
            user_id INT NOT NULL,
            movie_id INT NOT NULL,
            parent_id INT,
            comment_text TEXT NOT NULL,
            likes INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES comments (id) ON DELETE CASCADE
        )
    ''')
    
    # ===== SUBSCRIPTIONS =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id {auto_increment},
            user_id INT NOT NULL,
            plan_name VARCHAR(255) NOT NULL,
            price INT NOT NULL,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP NOT NULL,
            status VARCHAR(50) DEFAULT 'active',
            auto_renew {tinyint} DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # ===== PAYMENTS =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS payments (
            id {auto_increment},
            user_id INT NOT NULL,
            subscription_id INT,
            amount INT NOT NULL,
            currency VARCHAR(10) DEFAULT 'VND',
            payment_method VARCHAR(100) NOT NULL,
            payment_gateway VARCHAR(100),
            transaction_id VARCHAR(255) UNIQUE,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions (id)
        )
    ''')
    
    # ===== EPISODES (for series) =====
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS episodes (
            id {auto_increment},
            movie_id INT NOT NULL,
            episode_number INT NOT NULL,
            episode_name VARCHAR(255),
            video_url TEXT,
            server_name VARCHAR(100) DEFAULT 'Server 1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
        )
    ''')
    
    # ===== SEED DATA =====
    seed_initial_data(cursor)
    
    # ===== CREATE INDEXES FOR PERFORMANCE =====
    print("📊 Creating indexes for performance...")
    indexes = [
        # Movies table indexes
        "CREATE INDEX IF NOT EXISTS idx_movies_status_created ON movies(status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_movies_status_views ON movies(status, views)",
        "CREATE INDEX IF NOT EXISTS idx_movies_status_rating ON movies(status, imdb_rating)",
        "CREATE INDEX IF NOT EXISTS idx_movies_type ON movies(type)",
        "CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(release_year)",
        "CREATE INDEX IF NOT EXISTS idx_movies_slug ON movies(slug)",
        # Genres table index
        "CREATE INDEX IF NOT EXISTS idx_genres_slug ON genres(slug)",
        # Movie_genres junction table indexes
        "CREATE INDEX IF NOT EXISTS idx_movie_genres_genre ON movie_genres(genre_id, movie_id)",
        "CREATE INDEX IF NOT EXISTS idx_movie_genres_movie ON movie_genres(movie_id, genre_id)",
    ]
    
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except Exception:
            pass  # Index already exists
    
    print("✅ Indexes created successfully")
    
    # ===== CREATE FULLTEXT INDEXES FOR SEARCH OPTIMIZATION =====
    print("🔍 Creating FULLTEXT indexes for optimized search...")
    fulltext_indexes = [
        "CREATE FULLTEXT INDEX ft_title ON movies(title)",
        "CREATE FULLTEXT INDEX ft_original_title ON movies(original_title)",
        "CREATE FULLTEXT INDEX ft_description ON movies(description)",
        "CREATE FULLTEXT INDEX ft_search_all ON movies(title, original_title, description)",
    ]
    
    for ft_idx_sql in fulltext_indexes:
        try:
            cursor.execute(ft_idx_sql)
            print(f"  ✅ Created: {ft_idx_sql.split('INDEX')[1].split('ON')[0].strip()}")
        except Exception as e:
            # Check if error is "Duplicate key name" - means index already exists
            if "Duplicate key name" in str(e) or "already exists" in str(e).lower():
                index_name = ft_idx_sql.split('INDEX')[1].split('ON')[0].strip()
                print(f"  ℹ️  Already exists: {index_name}")
            else:
                print(f"  ⚠️  Failed to create FULLTEXT index: {str(e)}")
    
    print("✅ FULLTEXT indexes ready for fast search")
    
    conn.commit()
    conn.close()

def get_count_value(result):
    """Get count value from query result (MySQL DictCursor returns dict)"""
    if isinstance(result, dict):
        return list(result.values())[0]
    else:
        return result[0]

def seed_initial_data(cursor):
    """Insert sample data for streaming platform"""
    
    # Insert sample users
    cursor.execute('SELECT COUNT(*) FROM users')
    if get_count_value(cursor.fetchone()) == 0:
        sample_users = [
            ('John Doe', 'john@example.com', 'password123', 'free', 'free'),
            ('Jane VIP', 'jane@example.com', 'password123', 'user', 'vip'),
            ('Bob Premium', 'bob@example.com', 'password123', 'user', 'premium'),
            ('Admin User', 'admin@example.com', 'admin123', 'admin', 'premium')
        ]
        for name, email, password, role, tier in sample_users:
            cursor.execute(
                'INSERT INTO users (name, email, password_hash, role, subscription_tier) VALUES (?, ?, ?, ?, ?)',
                (name, email, hash_password(password), role, tier)
            )
    
    # Insert genres
    cursor.execute('SELECT COUNT(*) FROM genres')
    if get_count_value(cursor.fetchone()) == 0:
        genres_data = [
            ('Hành Động', 'hanh-dong', 'Phim hành động kịch tính'),
            ('Phiêu Lưu', 'phieu-luu', 'Phim phiêu lưu mạo hiểm'),
            ('Hài Hước', 'hai-huoc', 'Phim hài hước vui nhộn'),
            ('Tình Cảm', 'tinh-cam', 'Phim tình cảm lãng mạn'),
            ('Tâm Lý', 'tam-ly', 'Phim tâm lý xã hội'),
            ('Kinh Dị', 'kinh-di', 'Phim kinh dị ma quái'),
            ('Viễn Tưởng', 'vien-tuong', 'Phim viễn tưởng khoa học'),
            ('Cổ Trang', 'co-trang', 'Phim cổ trang lịch sử'),
            ('Hình Sự', 'hinh-su', 'Phim hình sự trinh thám'),
            ('Gia Đình', 'gia-dinh', 'Phim cho gia đình'),
            ('Chiến Tranh', 'chien-tranh', 'Phim chiến tranh lịch sử'),
            ('Thần Thoại', 'than-thoai', 'Phim thần thoại giả tưởng'),
            ('Tài Liệu', 'tai-lieu', 'Phim tài liệu'),
            ('Bí Ẩn', 'bi-an', 'Phim bí ẩn hồi hộp')
        ]
        for name, slug, desc in genres_data:
            cursor.execute(
                'INSERT INTO genres (name, slug, description) VALUES (?, ?, ?)',
                (name, slug, desc)
            )
    
    # Insert sample movies
    cursor.execute('SELECT COUNT(*) FROM movies')
    if get_count_value(cursor.fetchone()) == 0:
        sample_movies = [
            # PHIM LẺ (Movies)
            {
                'title': 'Avatar: The Way of Water',
                'original_title': 'Avatar: The Way of Water',
                'description': 'Jake Sully và Neytiri đã thành lập gia đình và đang cố gắng giữ gìn nó. Họ phải rời khỏi nhà và khám phá các vùng khác nhau của Pandora.',
                'release_year': 2022,
                'duration': 192,
                'country': 'USA',
                'language': 'English',
                'director': 'James Cameron',
                'cast': 'Sam Worthington, Zoe Saldana, Sigourney Weaver, Kate Winslet',
                'genres': 'action,adventure,sci-fi',
                'imdb_rating': 7.6,
                'poster_url': 'https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg',
                'backdrop_url': 'https://image.tmdb.org/t/p/original/s16H6tpK2utvwDtzZ8Qy4qm5Emw.jpg',
                'trailer_url': 'https://www.youtube.com/watch?v=d9MyW72ELq0',
                'video_url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'type': 'movie',
                'is_premium': 1
            },
            {
                'title': 'Guardians of the Galaxy Vol. 3',
                'original_title': 'Guardians of the Galaxy Vol. 3',
                'description': 'Peter Quill phải tập hợp đội của mình để bảo vệ vũ trụ và một trong những thành viên. Nếu không hoàn thành nhiệm vụ, đội có thể tan rã.',
                'release_year': 2023,
                'duration': 150,
                'country': 'USA',
                'language': 'English',
                'director': 'James Gunn',
                'cast': 'Chris Pratt, Zoe Saldana, Dave Bautista, Karen Gillan',
                'genres': 'action,comedy,sci-fi',
                'imdb_rating': 7.9,
                'poster_url': 'https://image.tmdb.org/t/p/w500/r2J02Z2OpNTctfOSN1Ydgii51I3.jpg',
                'backdrop_url': 'https://image.tmdb.org/t/p/original/5i3ghCXVLNhewrBjTesMgy4FHT6.jpg',
                'trailer_url': 'https://www.youtube.com/watch?v=u3V5KDHRQvk',
                'video_url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'type': 'movie',
                'is_premium': 0
            },
            {
                'title': 'Spider-Man: Across the Spider-Verse',
                'original_title': 'Spider-Man: Across the Spider-Verse',
                'description': 'Miles Morales trở lại với cuộc phiêu lưu hoành tráng qua đa vũ trụ cùng Gwen Stacy và đội ngũ Spider-People mới.',
                'release_year': 2023,
                'duration': 140,
                'country': 'USA',
                'language': 'English',
                'director': 'Joaquim Dos Santos, Kemp Powers, Justin K. Thompson',
                'cast': 'Shameik Moore, Hailee Steinfeld, Oscar Isaac',
                'genres': 'animation,action,adventure',
                'imdb_rating': 8.7,
                'poster_url': 'https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg',
                'backdrop_url': 'https://image.tmdb.org/t/p/original/tNGK2mkJiYMv2PjOYq2JjzQDd4s.jpg',
                'trailer_url': 'https://www.youtube.com/watch?v=cqGjhVJWtEg',
                'video_url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'type': 'movie',
                'is_premium': 0
            },
            # PHIM BỘ (Series)
            {
                'title': 'Stranger Things',
                'original_title': 'Stranger Things',
                'description': 'Khi một cậu bé biến mất, một thị trấn nhỏ phát hiện ra một bí ẩn liên quan đến thí nghiệm bí mật, lực lượng siêu nhiên đáng sợ và một cô gái kỳ lạ.',
                'release_year': 2023,
                'duration': 50,
                'country': 'USA',
                'language': 'English',
                'director': 'The Duffer Brothers',
                'cast': 'Millie Bobby Brown, Finn Wolfhard, Winona Ryder, David Harbour',
                'genres': 'drama,fantasy,horror',
                'imdb_rating': 8.7,
                'poster_url': 'https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg',
                'backdrop_url': 'https://image.tmdb.org/t/p/original/56v2KjBlU4XaOv9rVYEQypROD7P.jpg',
                'trailer_url': 'https://www.youtube.com/watch?v=b9EkMc79ZSU',
                'video_url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'type': 'series',
                'is_premium': 1
            },
            {
                'title': 'The Last of Us',
                'original_title': 'The Last of Us',
                'description': 'Sau một đại dịch toàn cầu tàn phá nền văn civiliz, Joel và Ellie phải đối mặt với những kẻ nhiễm bệnh và những kẻ tuyệt vọng khác trong hành trình vượt qua nước Mỹ.',
                'release_year': 2023,
                'duration': 60,
                'country': 'USA',
                'language': 'English',
                'director': 'Craig Mazin, Neil Druckmann',
                'cast': 'Pedro Pascal, Bella Ramsey, Anna Torv',
                'genres': 'action,drama,sci-fi',
                'imdb_rating': 8.8,
                'poster_url': 'https://image.tmdb.org/t/p/w500/uKvVjHNqB5VmOrdxqAt2F7J78ED.jpg',
                'backdrop_url': 'https://image.tmdb.org/t/p/original/uDgy6hyPd82kOHh6I95FLtLnj6p.jpg',
                'trailer_url': 'https://www.youtube.com/watch?v=uLtkt8BonwM',
                'video_url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'type': 'series',
                'is_premium': 1
            },
            {
                'title': 'Wednesday',
                'original_title': 'Wednesday',
                'description': 'Wednesday Addams học cách làm chủ khả năng ngoại cảm, ngăn chặn một cuộc giết người hàng loạt và giải quyết bí ẩn siêu nhiên từ 25 năm trước.',
                'release_year': 2022,
                'duration': 45,
                'country': 'USA',
                'language': 'English',
                'director': 'Tim Burton',
                'cast': 'Jenna Ortega, Gwendoline Christie, Emma Myers',
                'genres': 'comedy,fantasy,mystery',
                'imdb_rating': 8.1,
                'poster_url': 'https://image.tmdb.org/t/p/w500/9PFonBhy4cQy7Jz20NpMygczOkv.jpg',
                'backdrop_url': 'https://image.tmdb.org/t/p/original/iHSwvRVsRyxpX7FE7GbviaDvgGZ.jpg',
                'trailer_url': 'https://www.youtube.com/watch?v=Di310WS8zLk',
                'video_url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'type': 'series',
                'is_premium': 0
            }
        ]
        
        for movie in sample_movies:
            cursor.execute('''
                INSERT INTO movies (
                    title, original_title, description, release_year, duration,
                    country, language, director, cast, genres, imdb_rating,
                    poster_url, backdrop_url, trailer_url, video_url, type, is_premium
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                movie['title'], movie['original_title'], movie['description'],
                movie['release_year'], movie['duration'], movie['country'],
                movie['language'], movie['director'], movie['cast'],
                movie['genres'], movie['imdb_rating'], movie['poster_url'],
                movie['backdrop_url'], movie['trailer_url'], movie['video_url'],
                movie['type'], movie['is_premium']
            ))


@app.route('/')
def home():
    """Home route - serve streaming homepage"""
    return send_from_directory(PAGES_DIR, 'streaming.html')

@app.route('/login.html')
def login_page():
    """Serve the login/register page"""
    return send_from_directory(PAGES_DIR, 'login.html')

@app.route('/movie-detail.html')
def movie_detail_page():
    """Serve the movie detail page"""
    return send_from_directory(PAGES_DIR, 'movie-detail.html')

@app.route('/player.html')
def player_page():
    """Serve the video player page"""
    return send_from_directory(PAGES_DIR, 'player.html')

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return '', 204  # No content

@app.route('/api/image-proxy')
def image_proxy():
    """Proxy images to avoid CORS issues"""
    import requests
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return response.content, response.status_code, {
            'Content-Type': response.headers.get('Content-Type', 'image/jpeg'),
            'Cache-Control': 'public, max-age=86400'
        }
    except Exception:
        return '', 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from frontend/public directory (absolute paths)"""
    # Handle paths with subdirectories (css/, js/, images/, etc.)
    if '/' in filename:
        parts = filename.split('/')

        if parts[0] == 'css':
            return send_from_directory(CSS_DIR, '/'.join(parts[1:]))
        elif parts[0] == 'js':
            return send_from_directory(JS_DIR, '/'.join(parts[1:]))
        elif parts[0] == 'pages':
            return send_from_directory(PAGES_DIR, '/'.join(parts[1:]))

    # Handle direct files by extension
    if filename.endswith('.html'):
        return send_from_directory(PAGES_DIR, filename)
    elif filename.endswith('.css'):
        return send_from_directory(CSS_DIR, filename)
    elif filename.endswith('.js'):
        return send_from_directory(JS_DIR, filename)
    else:
        # Fallback to public root
        return send_from_directory(FRONTEND_PUBLIC_DIR, filename)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users from database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'data': users, 'count': len(users)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user with password"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not name or not email or not password:
            return jsonify({'success': False, 'error': 'Name, email and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Hash password and insert user
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            (name, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': {'id': user_id, 'name': name, 'email': email}
        }), 201
    except IntegrityError:
        return jsonify({'success': False, 'error': 'Email already exists'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user with email and password"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        print(f"🔐 Login attempt - Email: {email}")
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            print(f"❌ User not found: {email}")
            return jsonify({'success': False, 'error': 'Email or password is incorrect'}), 401
        
        print(f"✓ User found: {user['name']}")
        print(f"  Hash (first 50): {user['password_hash'][:50]}")
        
        # Verify password
        password_valid = verify_password(password, user['password_hash'])
        print(f"  Password valid: {password_valid}")
        
        if not password_valid:
            print("❌ Password verification failed")
            return jsonify({'success': False, 'error': 'Email or password is incorrect'}), 401
        
        # Store user in session
        session.permanent = True
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']
        session['user_subscription_tier'] = user.get('subscription_tier', 'free')
        
        print(f"✅ Session created for user: {user['name']}")
        print(f"   Session data: {dict(session)}")
        
        # Return user data (without password hash)
        user_data = {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'subscription_tier': user['subscription_tier'],
            'created_at': user['created_at']
        }
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': user_data
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    print(f"🔍 Check auth - Session data: {dict(session)}")  # Debug log
    if 'user_id' in session:
        print(f"✅ User authenticated: {session['user_name']}")  # Debug log
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name'],
                'role': session['user_role'],
                    'email': session.get('user_email', ''),
                    'subscription_tier': session.get('user_subscription_tier', 'free')
            }
        }), 200
    else:
        print("❌ User not authenticated - session empty")  # Debug log
        return jsonify({'success': True, 'authenticated': False}), 200

# @app.route('/api/users', methods=['POST'])
# def create_user():
#     """Create new user (legacy endpoint for compatibility)"""
#     try:
#         data = request.get_json()
#         name = data.get('name')
#         email = data.get('email')
#         password = data.get('password', 'defaultpass123')  # Default password if not provided
        
#         if not name or not email:
#             return jsonify({'success': False, 'error': 'Name and email are required'}), 400
        
#         conn = get_db()
#         cursor = conn.cursor()
#         password_hash = hash_password(password)
#         cursor.execute(
#             'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
#             (name, email, password_hash)
#         )
#         conn.commit()
#         user_id = cursor.lastrowid
#         conn.close()
        
#         return jsonify({
#             'success': True,
#             'message': 'User created successfully',
#             'data': {'id': user_id, 'name': name, 'email': email}
#         }), 201
#     except Exception as e:
#         # Handle duplicate email (IntegrityError from MySQL)
#         if 'email' in str(e).lower() or 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
#             return jsonify({'success': False, 'error': 'Email already exists'}), 400
#         return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Get single user by ID"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({'success': True, 'data': dict(user)})
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Update user profile"""
    # Prevent users from updating other users' profiles unless they are an admin
    if 'user_id' not in session or (session['user_id'] != user_id and session.get('user_role') != 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        
        if not name or not email:
            return jsonify({'success': False, 'error': 'Name and email are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email already exists for another user
        cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Update user
        cursor.execute('''
            UPDATE users 
            SET name = ?, email = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, email, user_id))
        
        conn.commit()
        updated = cursor.rowcount
        conn.close()
        
        if updated:
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/change-password', methods=['PUT'])
@login_required
def change_password(user_id):
    """Change user password"""
    if 'user_id' not in session or session['user_id'] != user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Current and new password required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current user
        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify current password
        if not verify_password(current_password, user['password_hash']):
            conn.close()
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # Update password
        new_hash = hash_password(new_password)
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_hash, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete user by ID"""
    # Only admin can delete users
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        
        if deleted:
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/bookings', methods=['POST'])
# def create_booking():
#     """Create new cinema booking"""
#     try:
#         data = request.get_json()
        
#         # Extract booking data
#         booking_code = data.get('bookingCode')
#         movie = data.get('movie')
#         showtime = data.get('showtime')
#         seats = data.get('seats')
#         customer = data.get('customer')
#         total_price = data.get('totalPrice')
        
#         # Validate required fields
#         if not all([booking_code, movie, showtime, seats, customer, total_price]):
#             return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
#         # Get user_id if logged in
#         user_id = session.get('user_id')
        
#         # Save booking
#         conn = get_db()
#         cursor = conn.cursor()
        
#         seats_str = ','.join([s['id'] for s in seats])
        
#         cursor.execute('''
#             INSERT INTO bookings 
#             (booking_code, user_id, movie_title, showtime_date, showtime_time, room, 
#              seats, customer_name, customer_phone, customer_email, payment_method, total_price)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             booking_code,
#             user_id,
#             movie['title'],
#             showtime['dateStr'],
#             showtime['time'],
#             showtime['room'],
#             seats_str,
#             customer['name'],
#             customer['phone'],
#             customer['email'],
#             customer['paymentMethod'],
#             total_price
#         ))
        
#         conn.commit()
#         booking_id = cursor.lastrowid
#         conn.close()
        
#         return jsonify({
#             'success': True,
#             'message': 'Booking created successfully',
#             'data': {
#                 'id': booking_id,
#                 'booking_code': booking_code
#             }
#         }), 201
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/bookings', methods=['GET'])
# @login_required
# def get_bookings():
#     """Get all bookings"""
#     try:
#         conn = get_db()
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC')
#         bookings = [dict(row) for row in cursor.fetchall()]
#         conn.close()
#         return jsonify({'success': True, 'data': bookings, 'count': len(bookings)})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/bookings/<booking_code>', methods=['GET'])
# @login_required
# def get_booking(booking_code):
#     """Get booking by code"""
#     try:
#         conn = get_db()
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM bookings WHERE booking_code = ?', (booking_code,))
#         booking = cursor.fetchone()
#         conn.close()
        
#         if booking:
#             return jsonify({'success': True, 'data': dict(booking)})
#         else:
#             return jsonify({'success': False, 'error': 'Booking not found'}), 404
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# ===== STREAMING PLATFORM APIs =====

@app.route('/api/movies', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def get_movies():
    """Get all movies or filter by parameters with sorting and pagination"""
    try:

        
        conn = get_db()
        cursor = conn.cursor()

        # Get query parameters
        search = request.args.get('search')
        genre = request.args.get('genre')
        year = request.args.get('year')
        is_premium = request.args.get('is_premium')
        country = request.args.get('country')
        min_rating = request.args.get('min_rating')
        content_type = request.args.get('type')  # 'movie' or 'series'
        sort = request.args.get('sort', 'created_at')  # created_at, imdb_rating, views
        order = request.args.get('order', 'desc').lower()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        where_clauses = ['status = ?']
        params = ['active']

        # Store search query for relevance scoring
        search_query = None
        search_mode = None
        if search:
            # Use smart search helper for better query building
            search_query, search_mode = smart_search.build_smart_search_query(search)
            if search_query and search_mode:
                # Title-only FULLTEXT search (case-insensitive by default)
                where_clauses.append(f'MATCH(title) AGAINST(? {search_mode})')
                params.append(search_query)

        if genre:
            where_clauses.append('genres LIKE ?')
            params.append(f'%{genre}%')

        if year:
            where_clauses.append('release_year = ?')
            params.append(year)

        if is_premium is not None:
            where_clauses.append('is_premium = ?')
            params.append(1 if is_premium == 'true' else 0)

        if country:
            where_clauses.append('country LIKE ?')
            params.append(f'%{country}%')
        
        if content_type:
            where_clauses.append('type = ?')
            params.append(content_type)

        if min_rating:
            where_clauses.append('imdb_rating >= ?')
            params.append(float(min_rating))

        where_sql = ' AND '.join(where_clauses)

        # Validate sort field
        allowed_sorts = ['created_at', 'updated_at', 'imdb_rating', 'views', 'release_year', 'title']
        if sort not in allowed_sorts:
            sort = 'updated_at'  # Default to updated_at for "New Releases"

        order_sql = 'DESC' if order == 'desc' else 'ASC'

        # Count total matching
        count_query = f'SELECT COUNT(*) as total FROM movies WHERE {where_sql}'
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total']

        # Pagination
        offset = (page - 1) * per_page

        # If search query exists, add relevance score to sort by match quality
        if search_query and search_mode:
            # Add relevance score column and prioritize it in sorting
            # Use same search mode for consistency
            query = f'''\
                SELECT *, MATCH(title) AGAINST(? {search_mode}) as relevance
                FROM movies 
                WHERE {where_sql} 
                ORDER BY relevance DESC, {sort} {order_sql}
                LIMIT ? OFFSET ?
            '''
            # Add search query for relevance calculation
            exec_params = [search_query] + list(params) + [per_page, offset]
        else:
            query = f'SELECT * FROM movies WHERE {where_sql} ORDER BY {sort} {order_sql} LIMIT ? OFFSET ?'
            exec_params = list(params) + [per_page, offset]

        cursor.execute(query, tuple(exec_params))
        movies = [dict(row) for row in cursor.fetchall()]
        
        # Remove relevance score from results (internal use only)
        if search_query:
            for movie in movies:
                movie.pop('relevance', None)
        
        conn.close()

        result = {
            'success': True,
            'data': movies,
            'count': len(movies),
            'total_count': total_count,
            'page': page,
            'per_page': per_page
        }
        

        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/movies/<int:movie_id>', methods=['GET'])
@cache.cached(timeout=300)
def get_movie_detail(movie_id):
    """Get movie detail by ID including episodes if series"""
    try:
        print(f"🔍 [API] Getting movie detail for ID: {movie_id}")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
        movie = cursor.fetchone()
        
        if not movie:
            print(f"❌ [API] Movie ID {movie_id} not found in database")
            conn.close()
            return jsonify({'success': False, 'error': 'Movie not found'}), 404
        
        print(f"✅ [API] Movie found: {movie.get('title', 'Unknown') if isinstance(movie, dict) else 'Movie data'}")
        
        # Update views count
        try:
            cursor.execute('UPDATE movies SET views = views + 1 WHERE id = ?', (movie_id,))
            conn.commit()
        except Exception as view_error:
            print(f"⚠️ [API] Could not update views: {view_error}")
            # Continue even if view update fails
        
        # Convert to dict if needed (MySQL DictCursor usually returns dict)
        movie_dict = dict(movie) if not isinstance(movie, dict) else movie
        
        # Get episodes if it's a series
        if movie_dict.get('type') == 'series':
            try:
                cursor.execute('''
                    SELECT id, episode_number, episode_name, video_url, duration, server_name
                    FROM episodes
                    WHERE movie_id = ?
                    ORDER BY episode_number ASC
                ''', (movie_id,))
                
                episodes_result = cursor.fetchall()
                
                if episodes_result:
                    # Convert episodes to list of dicts
                    episodes_list = []
                    for ep in episodes_result:
                        ep_dict = dict(ep) if not isinstance(ep, dict) else ep
                        episodes_list.append({
                            'id': ep_dict.get('id'),
                            'episode_number': ep_dict.get('episode_number'),
                            'name': ep_dict.get('episode_name') or f"Tập {ep_dict.get('episode_number')}",
                            'video_url': ep_dict.get('video_url'),
                            'duration': ep_dict.get('duration'),
                            'server_name': ep_dict.get('server_name', 'Server 1')
                        })
                    
                    movie_dict['episodes'] = episodes_list
                    movie_dict['total_episodes'] = len(episodes_list)
                    print(f"📺 [API] Added {len(episodes_list)} episodes to movie data")
                else:
                    movie_dict['episodes'] = []
                    movie_dict['total_episodes'] = 0
            except Exception as ep_error:
                print(f"⚠️ [API] Error loading episodes: {ep_error}")
                movie_dict['episodes'] = []
                movie_dict['total_episodes'] = 0
        else:
            # Not a series, no episodes
            movie_dict['episodes'] = []
            movie_dict['total_episodes'] = 0
        
        conn.close()
        
        print(f"📤 [API] Returning movie data: {len(movie_dict)} fields")
        return jsonify({'success': True, 'data': movie_dict})
        
    except Exception as e:
        print(f"❌ [API] Error in get_movie_detail: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/movies/<int:movie_id>/episodes/<int:episode_number>', methods=['GET'])
def get_episode_detail(movie_id, episode_number):
    """Get specific episode details for a series"""
    try:
        print(f"🔍 [API] Getting episode {episode_number} for movie ID: {movie_id}")
        
        conn = get_db()
        cursor = conn.cursor()
        
        # First verify the movie exists and is a series
        cursor.execute('SELECT type FROM movies WHERE id = ?', (movie_id,))
        movie = cursor.fetchone()
        
        if not movie:
            conn.close()
            return jsonify({'success': False, 'error': 'Movie not found'}), 404
        
        movie_dict = dict(movie) if not isinstance(movie, dict) else movie
        
        if movie_dict.get('type') != 'series':
            conn.close()
            return jsonify({'success': False, 'error': 'This is not a series'}), 400
        
        # Get the specific episode
        cursor.execute('''
            SELECT id, episode_number, episode_name, video_url, duration, server_name
            FROM episodes
            WHERE movie_id = ? AND episode_number = ?
        ''', (movie_id, episode_number))
        
        episode = cursor.fetchone()
        conn.close()
        
        if not episode:
            return jsonify({'success': False, 'error': 'Episode not found'}), 404
        
        episode_dict = dict(episode) if not isinstance(episode, dict) else episode
        
        print(f"✅ [API] Found episode {episode_number}")
        return jsonify({'success': True, 'data': episode_dict})
        
    except Exception as e:
        print(f"❌ [API] Error in get_episode_detail: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/movies/search', methods=['GET'])
@cache.cached(timeout=60, query_string=True)  # Cache search results for 1 minute
def search_movies():
    """Smart search movies using FULLTEXT indexes with fuzzy matching and synonym support"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 100))  # Allow custom limit
        
        if not query:
            return jsonify({'success': True, 'data': [], 'count': 0})
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Use smart search helper for intelligent query building
        search_query, search_mode = smart_search.build_smart_search_query(query)
        
        if not search_query or not search_mode:
            return jsonify({'success': True, 'data': [], 'count': 0})

        # Use FULLTEXT search with Boolean mode for wildcard support
        # This enables fuzzy/partial matching while maintaining speed
        cursor.execute(f'''
            SELECT *, 
                   MATCH(title) AGAINST(? {search_mode}) as relevance
            FROM movies 
            WHERE status = "active" 
              AND MATCH(title) AGAINST(? {search_mode})
            ORDER BY relevance DESC, imdb_rating DESC, views DESC
            LIMIT ?
        ''', (search_query, search_query, limit))
        
        movies = [dict(row) for row in cursor.fetchall()]
        
        # Fallback: if no FULLTEXT results and query is short, use LIKE with accent-insensitive collation
        if not movies and len(query.strip()) >= 1:
            normalized_q = smart_search.normalize_vietnamese(query).strip()
            cursor.execute('''
                SELECT * 
                FROM movies 
                WHERE status = "active" 
                  AND LOWER(title) COLLATE utf8mb4_unicode_ci LIKE CONCAT(?, '%')
                ORDER BY imdb_rating DESC, views DESC
                LIMIT ?
            ''', (normalized_q.lower(), limit))
            movies = [dict(row) for row in cursor.fetchall()]
        
        # Apply strict prefix priority + custom relevance boost for better ranking
        query_words = smart_search.normalize_vietnamese(query).split()
        for movie in movies:
            # Prefix flags
            f_full, f_first, f_other, match_cnt = smart_search.compute_prefix_flags(movie, query_words)
            movie['_p_full'] = f_full
            movie['_p_first'] = f_first
            movie['_p_other'] = f_other
            movie['_match_cnt'] = match_cnt
            # Calculate custom boost
            boost = smart_search.calculate_relevance_boost(movie, query_words)
            movie['_boost'] = boost
            # Remove internal relevance score
            movie.pop('relevance', None)

        # Re-sort: strict prefix priority first, then match count, then boost, rating, views
        movies.sort(
            key=lambda m: (
                m.get('_p_full', 0),
                m.get('_p_first', 0),
                m.get('_p_other', 0),
                m.get('_match_cnt', 0),
                float(m.get('_boost', 0) or 0),
                float(m.get('imdb_rating', 0) or 0),
                int(m.get('views', 0) or 0)
            ),
            reverse=True
        )
        
        # Remove boost from final results
        for movie in movies:
            movie.pop('_boost', None)
            movie.pop('_p_full', None)
            movie.pop('_p_first', None)
            movie.pop('_p_other', None)
            movie.pop('_match_cnt', None)
        
        conn.close()
        
        return jsonify({'success': True, 'data': movies, 'count': len(movies), 'total': len(movies)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search/autocomplete', methods=['GET'])
@cache.cached(timeout=60, query_string=True)  # Cache for 60 seconds per query
def search_autocomplete():
    """Get autocomplete suggestions for search query"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))

        if not query or len(query) < 2:
            return jsonify({'success': True, 'data': [], 'count': 0})

        conn = get_db()
        cursor = conn.cursor()

        # Build smart search query
        search_query, search_mode = smart_search.build_smart_search_query(query)

        # Execute FULLTEXT search with smart query
        # Get more results for better ranking (we'll filter later)
        sql = f'''
            SELECT m.*, 
                   GROUP_CONCAT(DISTINCT g.name) as genres,
                   m.imdb_rating as rating,
                   m.views as views
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE MATCH(m.title) AGAINST(? {search_mode})
              AND m.status = "active"
            GROUP BY m.id
            LIMIT 200
        '''

        cursor.execute(sql, (search_query,))
        results = [dict(row) for row in cursor.fetchall()]
        
        # Fallback: if no FULLTEXT results, use LIKE with accent-insensitive collation
        if not results and len(query.strip()) >= 1:
            normalized_q = smart_search.normalize_vietnamese(query).strip()
            sql_fallback = '''
                SELECT m.*, 
                       GROUP_CONCAT(DISTINCT g.name) as genres,
                       m.imdb_rating as rating,
                       m.views as views
                FROM movies m
                LEFT JOIN movie_genres mg ON m.id = mg.movie_id
                LEFT JOIN genres g ON mg.genre_id = g.id
                WHERE LOWER(m.title) COLLATE utf8mb4_unicode_ci LIKE CONCAT(?, '%')
                  AND m.status = "active"
                GROUP BY m.id
                ORDER BY m.imdb_rating DESC, m.views DESC
                LIMIT 200
            '''
            cursor.execute(sql_fallback, (normalized_q.lower(),))
            results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()

        if not results:
            return jsonify({'success': True, 'data': [], 'count': 0, 'total': 0})

        # Apply strict prefix priority + custom relevance boost
        query_words = smart_search.normalize_vietnamese(query).split()

        for movie in results:
            f_full, f_first, f_other, match_cnt = smart_search.compute_prefix_flags(movie, query_words)
            movie['_p_full'] = f_full
            movie['_p_first'] = f_first
            movie['_p_other'] = f_other
            movie['_match_cnt'] = match_cnt
            boost = smart_search.calculate_relevance_boost(movie, query_words)
            movie['boost'] = boost

            # Highlight keywords in title
            movie['title_highlighted'] = smart_search.highlight_keywords(
                movie.get('title', ''), 
                query_words
            )

        # Sort by prefix priority first, then match count, then boost, rating, views
        results.sort(
            key=lambda x: (
                x.get('_p_full', 0),
                x.get('_p_first', 0),
                x.get('_p_other', 0),
                x.get('_match_cnt', 0),
                float(x.get('boost', 0) or 0),
                float(x.get('rating', 0) or 0),
                int(x.get('views', 0) or 0)
            ),
            reverse=True
        )

        # Return top N results
        top_results = results[:limit]

        # Remove internal boost score before returning
        for movie in top_results:
            movie.pop('boost', None)
            movie.pop('_p_full', None)
            movie.pop('_p_first', None)
            movie.pop('_p_other', None)
            movie.pop('_match_cnt', None)

        return jsonify({
            'success': True,
            'data': top_results,
            'count': len(top_results),
            'total': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/movies/mood/<mood>', methods=['GET'])
def get_movies_by_mood(mood):
    """Get movies filtered by mood/emotion - NEW FEATURE 🎭"""
    try:
        # Mood to genres mapping
        mood_genre_map = {
            'happy': ['Comedy', 'Family', 'Animation'],
            'sad': ['Drama', 'Romance'],
            'relaxed': ['Documentary', 'Drama'],
            'energetic': ['Action', 'Adventure', 'Thriller'],
            'thoughtful': ['Mystery', 'Sci-Fi', 'Drama'],
            'romantic': ['Romance', 'Drama']
        }
        
        if mood not in mood_genre_map:
            return jsonify({'success': False, 'error': 'Invalid mood'}), 400
        
        target_genres = mood_genre_map[mood]
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get movies that match any of the mood's genres
        placeholders = ','.join(['?' for _ in target_genres])
        query = f'''
            SELECT DISTINCT m.*, GROUP_CONCAT(g.name) as genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE m.status = "active" 
            AND g.name IN ({placeholders})
            GROUP BY m.id
            ORDER BY m.imdb_rating DESC, m.views DESC
            LIMIT 20
        '''
        
        cursor.execute(query, target_genres)
        movies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True, 
            'data': movies, 
            'count': len(movies),
            'mood': mood,
            'genres': target_genres
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/genres', methods=['GET'])
@cache.cached(timeout=900)  # Cache for 15 minutes; clear via /api/cache/clear
def get_genres():
    """Get all genres with movie count"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.*, COUNT(mg.movie_id) as movie_count
            FROM genres g
            LEFT JOIN movie_genres mg ON g.id = mg.genre_id
            GROUP BY g.id
            ORDER BY g.name
        ''')
        genres = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        result = {'success': True, 'data': genres, 'count': len(genres)}
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/genres/<int:genre_id>/movies', methods=['GET'])
@cache.cached(timeout=300, query_string=True) # Cache for 5 minutes
def get_movies_by_genre(genre_id):
    """Get all movies in a specific genre with pagination"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Get genre info
        cursor.execute('SELECT * FROM genres WHERE id = %s', (genre_id,))
        genre = cursor.fetchone()
        if not genre:
            conn.close()
            return jsonify({'success': False, 'error': 'Genre not found'}), 404
        
        # Count total movies in this genre
        cursor.execute('''
            SELECT COUNT(*) as total
            FROM movie_genres mg
            JOIN movies m ON mg.movie_id = m.id
            WHERE mg.genre_id = %s AND m.status = 'active'
        ''', (genre_id,))
        total_count = cursor.fetchone()['total']
        
        # Get movies
        cursor.execute('''
            SELECT m.*
            FROM movie_genres mg
            JOIN movies m ON mg.movie_id = m.id
            WHERE mg.genre_id = %s AND m.status = 'active'
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s
        ''', (genre_id, per_page, offset))
        movies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        result = {
            'success': True,
            'genre': dict(genre),
            'data': movies,
            'count': len(movies),
            'total_count': total_count,
            'page': page,
            'per_page': per_page
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
@login_required
def clear_all_cache():
    """Clear all cache (admin only)"""
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    cache.clear()
    return jsonify({'success': True, 'message': 'Cache cleared'})

@app.route('/api/watch-history', methods=['GET', 'POST', 'DELETE'])
@login_required
def watch_history():
    """Get, update or delete watch history"""
    if request.method == 'GET':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT wh.*, m.title, m.poster_url, m.release_year, m.imdb_rating, m.type, m.genres, m.description
                FROM watch_history wh
                JOIN movies m ON wh.movie_id = m.id
                WHERE wh.user_id = ?
                ORDER BY wh.last_watched DESC
                LIMIT 20
            ''', (session['user_id'],))
            
            history = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({'success': True, 'data': history})
        except Exception as e:
            print(f"Error getting watch history: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            movie_id = data.get('movie_id')
            progress = data.get('progress', 0)
            
            if not movie_id:
                return jsonify({'success': False, 'error': 'movie_id required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            
            # Check if entry exists
            cursor.execute('SELECT id FROM watch_history WHERE user_id = ? AND movie_id = ?',
                         (session['user_id'], movie_id))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE watch_history 
                    SET progress = ?, completed = ?, last_watched = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND movie_id = ?
                ''', (progress, 1 if progress >= 95 else 0, session['user_id'], movie_id))
            else:
                cursor.execute('''
                    INSERT INTO watch_history (user_id, movie_id, progress, completed)
                    VALUES (?, ?, ?, ?)
                ''', (session['user_id'], movie_id, progress, 1 if progress >= 95 else 0))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Watch history updated'})
        except Exception as e:
            print(f"Error updating watch history: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # DELETE - Clear all watch history
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM watch_history WHERE user_id = ?', (session['user_id'],))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Watch history cleared'})
        except Exception as e:
            print(f"Error clearing watch history: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
@login_required
def favorites():
    """Manage user favorites"""
    if request.method == 'GET':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT f.*, m.title, m.poster_url, m.release_year, m.imdb_rating, m.is_premium,
                       m.type, m.genres, m.description
                FROM favorites f
                JOIN movies m ON f.movie_id = m.id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
            ''', (session['user_id'],))
            
            favorites_list = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({'success': True, 'data': favorites_list})
        except Exception as e:
            print(f"Error getting favorites: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            movie_id = data.get('movie_id')
            
            if not movie_id:
                return jsonify({'success': False, 'error': 'movie_id required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                cursor.execute('INSERT INTO favorites (user_id, movie_id) VALUES (?, ?)',
                             (session['user_id'], movie_id))
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': 'Added to favorites'})
            except Exception as inner_e:
                conn.close()
                # Handle duplicate favorite (IntegrityError from MySQL)
                if 'duplicate' in str(inner_e).lower() or 'unique' in str(inner_e).lower():
                    return jsonify({'success': False, 'error': 'Already in favorites'}), 400
                print(f"Error adding favorite: {inner_e}")
                return jsonify({'success': False, 'error': str(inner_e)}), 500
        except Exception as e:
            print(f"Error in POST favorites: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # DELETE
        try:
            data = request.get_json() or {}
            movie_id = data.get('movie_id')
            
            if not movie_id:
                return jsonify({'success': False, 'error': 'movie_id required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM favorites WHERE user_id = ? AND movie_id = ?',
                         (session['user_id'], movie_id))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Removed from favorites'})
        except Exception as e:
            print(f"Error deleting favorite: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites/<int:movie_id>', methods=['DELETE'])
@login_required
def delete_favorite(movie_id):
    """Delete a favorite by movie_id"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE user_id = ? AND movie_id = ?',
                     (session['user_id'], movie_id))
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Removed from favorites'})
        else:
            return jsonify({'success': False, 'error': 'Favorite not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews', methods=['GET', 'POST'])
def reviews():
    """Get or create reviews"""
    if request.method == 'GET':
        try:
            movie_id = request.args.get('movie_id')
            if not movie_id:
                return jsonify({'success': False, 'error': 'movie_id required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, u.name as user_name
                FROM reviews r
                JOIN users u ON r.user_id = u.id
                WHERE r.movie_id = ?
                ORDER BY r.created_at DESC
            ''', (movie_id,))
            
            reviews_list = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({'success': True, 'data': reviews_list})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # POST
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            movie_id = data.get('movie_id')
            rating = data.get('rating')
            review_text = data.get('review_text', '')
            
            if not user_id or not movie_id or not rating:
                return jsonify({'success': False, 'error': 'user_id, movie_id, and rating required'}), 400
            
            if rating < 1 or rating > 5:
                return jsonify({'success': False, 'error': 'rating must be between 1 and 5'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reviews (user_id, movie_id, rating, review_text)
                VALUES (?, ?, ?, ?)
            ''', (user_id, movie_id, rating, review_text))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Review submitted'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/comments', methods=['GET', 'POST'])
def comments():
    """Get or create comments"""
    if request.method == 'GET':
        try:
            movie_id = request.args.get('movie_id')
            if not movie_id:
                return jsonify({'success': False, 'error': 'movie_id required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, u.name as user_name
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.movie_id = ? AND c.parent_id IS NULL
                ORDER BY c.created_at DESC
            ''', (movie_id,))
            
            comments_list = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({'success': True, 'data': comments_list})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # POST
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            movie_id = data.get('movie_id')
            comment_text = data.get('comment_text')
            parent_id = data.get('parent_id')
            
            if not user_id or not movie_id or not comment_text:
                return jsonify({'success': False, 'error': 'user_id, movie_id, and comment_text required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comments (user_id, movie_id, parent_id, comment_text)
                VALUES (?, ?, ?, ?)
            ''', (user_id, movie_id, parent_id, comment_text))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Comment posted'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscription/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    plans = [
        {
            'id': 'free',
            'name': 'Miễn phí',
            'price': 0,
            'duration_days': 0,
            'features': ['Xem phim miễn phí', 'Quảng cáo', 'Chất lượng 720p'],
            'color': '#999999'
        },
        {
            'id': 'vip',
            'name': 'VIP',
            'price': 79000,
            'duration_days': 30,
            'features': ['Không quảng cáo', 'Chất lượng 1080p', 'Xem offline', 'Phim VIP'],
            'color': '#9c27b0'
        },
        {
            'id': 'premium',
            'name': 'Premium',
            'price': 149000,
            'duration_days': 30,
            'features': ['Tất cả tính năng VIP', 'Chất lượng 4K', 'Xem trên 4 thiết bị', 'Phim độc quyền'],
            'color': '#ff9800'
        }
    ]
    
    return jsonify({'success': True, 'data': plans})

@app.route('/api/subscription/subscribe', methods=['POST'])
def subscribe():
    """Subscribe to a plan"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        plan_id = data.get('plan_id')
        payment_method = data.get('payment_method')
        
        if not user_id or not plan_id:
            return jsonify({'success': False, 'error': 'user_id and plan_id required'}), 400
        
        # Get plan details
        plans = {
            'vip': {'name': 'VIP', 'price': 79000, 'days': 30},
            'premium': {'name': 'Premium', 'price': 149000, 'days': 30}
        }
        
        if plan_id not in plans:
            return jsonify({'success': False, 'error': 'Invalid plan'}), 400
        
        plan = plans[plan_id]
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Create subscription
        cursor.execute('''
            INSERT INTO subscriptions (user_id, plan_name, price, end_date, status)
            VALUES (?, ?, ?, datetime('now', '+' || ? || ' days'), 'active')
        ''', (user_id, plan['name'], plan['price'], plan['days']))
        
        subscription_id = cursor.lastrowid
        
        # Update user subscription tier
        cursor.execute('''
            UPDATE users 
            SET subscription_tier = ?, subscription_expires = datetime('now', '+' || ? || ' days')
            WHERE id = ?
        ''', (plan_id, plan['days'], user_id))
        
        # Create payment record
        import secrets
        transaction_id = secrets.token_hex(16)
        
        cursor.execute('''
            INSERT INTO payments (user_id, subscription_id, amount, payment_method, transaction_id, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
        ''', (user_id, subscription_id, plan['price'], payment_method or 'card', transaction_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Đăng ký {plan["name"]} thành công!',
            'transaction_id': transaction_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== ADMIN APIs =====

@app.route('/api/admin/movies', methods=['POST'])
def admin_create_movie():
    """Admin: Create new movie"""
    try:
        data = request.get_json()
        
        required_fields = ['title']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO movies (
                title, original_title, description, release_year, duration,
                country, language, director, cast, genres, imdb_rating,
                poster_url, backdrop_url, trailer_url, video_url, is_premium, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title'),
            data.get('original_title'),
            data.get('description'),
            data.get('release_year'),
            data.get('duration'),
            data.get('country'),
            data.get('language'),
            data.get('director'),
            data.get('cast'),
            data.get('genres'),
            data.get('imdb_rating'),
            data.get('poster_url'),
            data.get('backdrop_url'),
            data.get('trailer_url'),
            data.get('video_url'),
            data.get('is_premium', 0),
            data.get('status', 'active')
        ))
        
        conn.commit()
        movie_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Movie created', 'id': movie_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/movies/<int:movie_id>', methods=['PUT'])
def admin_update_movie(movie_id):
    """Admin: Update movie"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE movies SET
                title = ?, original_title = ?, description = ?, release_year = ?,
                duration = ?, country = ?, language = ?, director = ?, cast = ?,
                genres = ?, imdb_rating = ?, poster_url = ?, backdrop_url = ?,
                trailer_url = ?, video_url = ?, is_premium = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('title'),
            data.get('original_title'),
            data.get('description'),
            data.get('release_year'),
            data.get('duration'),
            data.get('country'),
            data.get('language'),
            data.get('director'),
            data.get('cast'),
            data.get('genres'),
            data.get('imdb_rating'),
            data.get('poster_url'),
            data.get('backdrop_url'),
            data.get('trailer_url'),
            data.get('video_url'),
            data.get('is_premium', 0),
            data.get('status', 'active'),
            movie_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Movie updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/movies/<int:movie_id>', methods=['DELETE'])
def admin_delete_movie(movie_id):
    """Admin: Delete movie"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Movie deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get movie recommendations for user"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            # Return popular movies for non-logged in users
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM movies 
                WHERE status = 'active'
                ORDER BY views DESC, imdb_rating DESC
                LIMIT 10
            ''')
            movies = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return jsonify({'success': True, 'data': movies})
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user's favorite genres from watch history
        cursor.execute('''
            SELECT m.genres
            FROM watch_history wh
            JOIN movies m ON wh.movie_id = m.id
            WHERE wh.user_id = ?
            ORDER BY wh.last_watched DESC
            LIMIT 10
        ''', (user_id,))
        
        user_genres = []
        for row in cursor.fetchall():
            if row['genres']:
                user_genres.extend(row['genres'].split(','))
        
        if not user_genres:
            # Return popular movies
            cursor.execute('''
                SELECT * FROM movies 
                WHERE status = 'active'
                ORDER BY views DESC, imdb_rating DESC
                LIMIT 10
            ''')
        else:
            # Find movies with similar genres
            most_common_genre = max(set(user_genres), key=user_genres.count)
            cursor.execute('''
                SELECT * FROM movies 
                WHERE status = 'active' AND genres LIKE ?
                ORDER BY imdb_rating DESC, views DESC
                LIMIT 10
            ''', (f'%{most_common_genre}%',))
        
        recommendations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'data': recommendations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== RUN SERVER =====
if __name__ == '__main__':
    print('\n' + '='*70)
    print('🎬  CGV STREAMING - MOVIE PLATFORM')
    print('='*70)
    print('\n🚀 Initializing database...')
    init_db()
    print('✅ Database initialized successfully!\n')
    
    print('🌐 Starting Flask server...')
    print('━'*70)
    print('� Server Status: ONLINE')
    print('🔗 Main URL:      http://localhost:5000')
    print('� Login Page:    http://localhost:5000/login.html')
    print('🎥 Movies Page:   http://localhost:5000/streaming.html')
    print('━'*70)
    print('💡 Press CTRL+C to stop the server')
    print('='*70 + '\n')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
