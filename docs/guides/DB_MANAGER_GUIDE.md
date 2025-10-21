# Database Manager - Hướng Dẫn Sử Dụng

## 📋 Tổng Quan

File `db_manager.py` là công cụ quản lý database thống nhất, gộp tất cả các chức năng:
- ✅ Kết nối database (MySQL/SQLite)
- ✅ Khởi tạo MySQL database
- ✅ Test kết nối
- ✅ Reset database
- ✅ Hiển thị thông tin database

## 🚀 Cách Sử Dụng

### 1. Import trong code Python

```python
from db_manager import get_db

# Sử dụng database connection
with get_db() as db:
    cursor = db.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
```

### 2. Chạy từ Command Line

#### Test kết nối
```bash
python db_manager.py --test
# hoặc
python db_manager.py -t
```

Hiển thị:
- Loại database (MySQL/SQLite)
- Thông tin kết nối
- Version
- Danh sách bảng và số lượng records

#### Hiển thị thông tin
```bash
python db_manager.py --info
# hoặc
python db_manager.py -i
```

#### Setup MySQL database
```bash
python db_manager.py --setup
# hoặc
python db_manager.py -s
```

Chức năng:
- Tạo database `cgv_streaming` (nếu chưa có)
- Sử dụng charset utf8mb4 (hỗ trợ tiếng Việt)

#### Reset database
```bash
python db_manager.py --reset
# hoặc
python db_manager.py -r
```

⚠️ **CẢNH BÁO**: Xóa toàn bộ database và tạo lại!

#### Trợ giúp
```bash
python db_manager.py --help
# hoặc
python db_manager.py -h
```

#### Chạy không có tham số
```bash
python db_manager.py
```
Mặc định sẽ chạy test kết nối.

## 🔧 Các Hàm Chính

### Connection Functions

#### `get_db()`
Lấy database connection (MySQL hoặc SQLite tùy cấu hình)

```python
from db_manager import get_db

db = get_db()
cursor = db.cursor()
# ... làm việc với database
db.close()

# Hoặc dùng context manager
with get_db() as db:
    cursor = db.cursor()
    # ... tự động commit và close
```

### Setup Functions

#### `create_mysql_database()`
Tạo MySQL database

```python
from db_manager import create_mysql_database

success, message = create_mysql_database()
if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

#### `drop_mysql_database()`
Xóa MySQL database

```python
from db_manager import drop_mysql_database

success, message = drop_mysql_database()
```

#### `reset_mysql_database()`
Reset database (drop và recreate)

```python
from db_manager import reset_mysql_database

success, message = reset_mysql_database()
```

### Info Functions

#### `get_database_info()`
Lấy thông tin database

```python
from db_manager import get_database_info

info = get_database_info()
print(f"Type: {info['type']}")
print(f"Version: {info['version']}")
print(f"Tables: {info['tables']}")
print(f"Table counts: {info['table_counts']}")
```

#### `test_connection()`
Test và hiển thị thông tin kết nối

```python
from db_manager import test_connection

success = test_connection()
if success:
    print("Kết nối thành công!")
```

## 📦 Class và Wrapper

### `MySQLCursorWrapper`
Wrapper tự động chuyển đổi placeholder từ `?` (SQLite) sang `%s` (MySQL)

### `DatabaseConnection`
Class quản lý kết nối database

```python
from db_manager import DatabaseConnection

conn = DatabaseConnection()
cursor = conn.cursor()
# ... làm việc với database
conn.commit()
conn.close()
```

## ⚙️ Cấu hình (.env)

```env
# Bật MySQL
USE_MYSQL=true

# Thông tin MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1732005
MYSQL_DATABASE=cgv_streaming
```

## 🔄 Workflow Thông Thường

### Lần đầu setup:

```bash
# 1. Tạo file .env với cấu hình MySQL
# 2. Setup database
python db_manager.py --setup

# 3. Chạy app để tạo tables và insert data
python app.py

# 4. Verify
python db_manager.py --info
```

### Hàng ngày:

```bash
# Test kết nối trước khi chạy app
python db_manager.py --test

# Chạy ứng dụng
python app.py
```

### Khi cần reset:

```bash
# Reset database (xóa toàn bộ data)
python db_manager.py --reset

# Chạy lại app để tạo lại tables
python app.py
```

## 📊 Output Examples

### Test Connection
```
============================================================
DATABASE CONNECTION TEST
============================================================

📋 Configuration:
   Type: MySQL
   Host: localhost
   Port: 3306
   User: root
   Database: cgv_streaming

✅ Connected successfully!
   Version: 9.4.0

📊 Tables (10):
   - comments: 0 rows
   - favorites: 0 rows
   - genres: 15 rows
   - movie_genres: 0 rows
   - movies: 6 rows
   - payments: 0 rows
   - reviews: 0 rows
   - subscriptions: 0 rows
   - users: 4 rows
   - watch_history: 0 rows

============================================================
```

### Database Info
```
============================================================
DATABASE INFORMATION
============================================================

Type: MySQL
Version: 9.4.0
Database: cgv_streaming

Tables: 10
  - comments: 0 rows
  - favorites: 0 rows
  - genres: 15 rows
  - movie_genres: 0 rows
  - movies: 6 rows
  - payments: 0 rows
  - reviews: 0 rows
  - subscriptions: 0 rows
  - users: 4 rows
  - watch_history: 0 rows
```

## 🎯 So sánh với files cũ

### Trước (3 files):
- `db_manager.py` - Chỉ connection
- `init_mysql.py` - Khởi tạo database
- `setup_mysql.py` - Tạo schema

### Bây giờ (1 file):
- `db_manager.py` - TẤT CẢ chức năng trong 1 file!

### Files có thể XÓA:
- ❌ `init_mysql.py` - Đã gộp vào `db_manager.py`
- ✅ `setup_mysql.py` - GIỮ LẠI nếu cần schema cụ thể
- ❌ `test_mysql_connection.py` - Thay bằng `python db_manager.py --test`
- ❌ `verify_data.py` - Thay bằng `python db_manager.py --info`
- ❌ `check_schema.py` - Thay bằng `python db_manager.py --info`

## 💡 Tips & Tricks

### 1. Quick test trước khi code
```bash
python db_manager.py -t
```

### 2. Check data nhanh
```bash
python db_manager.py -i | grep rows
```

### 3. Reset nhanh (no confirmation trong code)
```python
from db_manager import reset_mysql_database
success, msg = reset_mysql_database()
```

### 4. Kiểm tra kết nối trong code
```python
from db_manager import test_connection
if not test_connection():
    print("Database không available!")
    exit(1)
```

## 🐛 Troubleshooting

### Lỗi: "MySQL connection failed"
```bash
# 1. Check MySQL service
net start MySQL80

# 2. Test lại
python db_manager.py --test
```

### Lỗi: "Database does not exist"
```bash
# Setup database
python db_manager.py --setup
```

### Lỗi: "Access denied"
```bash
# Kiểm tra password trong .env
# Đảm bảo MYSQL_PASSWORD=1732005
```

## 📚 Tài Liệu Liên Quan

- `MYSQL_SETUP.md` - Hướng dẫn setup MySQL chi tiết
- `MIGRATION_COMPLETE.md` - Tài liệu migration từ SQLite
- `README.md` - Tài liệu chính của project

## 🎉 Tóm Tắt

File `db_manager.py` mới là **ALL-IN-ONE** solution cho database management:
- ✅ Kết nối database
- ✅ Setup/Reset database
- ✅ Test và verify
- ✅ Hiển thị thông tin
- ✅ Command line interface
- ✅ Import như library

**Một file cho mọi nhu cầu database!** 🚀
