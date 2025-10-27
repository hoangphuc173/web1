# 🎬 CGV Streaming Platform

Nền tảng xem phim trực tuyến với tính năng tự động import phim từ OPhim API.

## 📁 Cấu trúc Project

```
web1/
├── backend/                      # Backend API & Services
│   ├── app.py                   # Flask application chính
│   ├── db_manager.py            # Database manager (MySQL)
│   ├── requirements.txt         # Python dependencies
│   ├── config/                  # Configuration
│   └── scripts/                 # Import & utility scripts
│       ├── ophim_import_v3.py   # OPhim API importer
│       └── setup_fulltext_indexes.py  # Fulltext search setup
│
├── frontend/                     # Frontend files
│   └── public/
│       ├── pages/               # HTML pages
│       │   ├── login.html
│       │   ├── streaming.html
│       │   ├── movie-detail.html
│       │   ├── player.html
│       │   ├── browse.html
│       │   ├── profile.html
│       │   └── settings.html
│       ├── css/                 # Stylesheets
│       └── js/                  # JavaScript files
│           └── core/            # Core modules
│
├── docker-compose.yml           # Docker compose configuration
├── Dockerfile                   # Docker container definition
├── docker-entrypoint.sh        # Container startup script
└── README.md                    # Documentation
```

## ⚡ Quick Start (3 phút)

```bash
# 1. Tải về từ Git
git clone <repository-url>
cd web1

# 2. Chạy với Docker (khuyến nghị)
docker-compose up -d --build

# 3. Truy cập hệ thống
# Main: http://localhost:5000
# Login: http://localhost:5000/login.html
# Movies: http://localhost:5000/streaming.html
```

**✨ Auto-import chạy tự động mỗi 3 phút! Không cần cấu hình thêm.**

---

## 🚀 Hướng dẫn cài đặt chi tiết

### Yêu cầu hệ thống

- Docker
- Docker Compose
- 4GB RAM trở lên

### 1. Tải từ Git và khởi chạy nhanh

```bash
# Clone repository (HTTPS)
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>

# Hoặc nếu đã có mã nguồn sẵn (ví dụ thư mục 'web1')
cd web1

# Khởi chạy bằng Docker
docker-compose up -d --build
```

Nếu tải file .zip từ Git: giải nén, mở terminal tại thư mục dự án rồi chạy `docker-compose up -d --build`.

### 2. Khởi động hệ thống với Docker

```bash
# Build và start services
docker-compose up -d --build

# Hoặc chạy ở foreground để xem logs
docker-compose up
```

### 3. Truy cập hệ thống

- **Main URL**: http://localhost:5000
- **Login Page**: http://localhost:5000/login.html
- **Movies Page**: http://localhost:5000/streaming.html

### 4. Quản lý Docker

```bash
# Xem logs
docker-compose logs -f backend

# Dừng services
docker-compose down

# Dừng và xóa volumes (database)
docker-compose down -v

# Restart service
docker-compose restart backend
```

---

## 💻 Cài đặt môi trường phát triển (Development Manual)

Nếu muốn chạy thủ công không dùng Docker (để phát triển/debug):

### Yêu cầu cho Development

- **Python 3.11+**
- **MySQL 8.0** hoặc Docker chỉ cho MySQL
- **Git** (đã cài đặt)

### 1. Cài đặt Python Dependencies

```bash
# Vào thư mục backend
cd backend

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Kích hoạt virtual environment
# Trên Windows:
venv\Scripts\activate
# Trên Linux/Mac:
# source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cài đặt MySQL

#### Option A: Dùng Docker chỉ cho MySQL

```bash
# Chạy MySQL container
docker run -d \
  --name cgv-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=cgv_streaming \
  -p 3306:3306 \
  mysql:8.0
```

#### Option B: Cài MySQL trực tiếp

Tải MySQL từ: https://dev.mysql.com/downloads/mysql/

Hoặc dùng XAMPP/WAMP (Windows) / Homebrew (Mac)

### 3. Cấu hình Database

Tạo file `backend/.env`:

```env
# Database Configuration
USE_MYSQL=true
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=cgv_streaming

# Flask Configuration
FLASK_ENV=development
```

### 4. Khởi tạo Database

```bash
# Chắc chắn đang ở thư mục backend
cd backend

# Setup FULLTEXT indexes cho search
python scripts/setup_fulltext_indexes.py

# Import phim ban đầu (optional)
python scripts/ophim_import_v3.py --pages 5 --check-update
```

### 5. Chạy Flask Server

```bash
# Từ thư mục backend
python app.py
```

Server sẽ chạy tại: `http://localhost:5000`

### 6. Import Phim (Manual)

```bash
# Vào thư mục backend
cd backend

# Import phim
python scripts/ophim_import_v3.py --pages 10 --check-update

# Import theo thể loại
python scripts/ophim_import_v3.py --genre phim-le --pages 3

# Import liên tục (auto-refresh)
python scripts/ophim_import_v3.py --continuous --interval 180
```

### 7. Truy cập Frontend

Đảm bảo static files có thể truy cập:
- Mở trình duyệt: http://localhost:5000
- Login: http://localhost:5000/login.html
- Movies: http://localhost:5000/streaming.html

### Lưu ý Development

- **Backend**: Chạy tại `http://localhost:5000` (cả Docker và development)
- **MySQL**: Database chạy tại `localhost:3306` (dùng chung port với local)
- **Logs**: Sẽ hiển thị trong terminal
- **Debug**: Để debug trong development, set `debug=True` trong `app.py`

---

## ✨ Tính năng chính

### 🎬 User Features
- Xem phim với player tích hợp
- Đăng nhập / Đăng ký người dùng
- Yêu thích & Lịch sử xem
- Tìm kiếm phim với FULLTEXT search (có dấu/không dấu)
- Phân loại phim (Phim lẻ, Phim bộ, Thể loại)

### 🤖 Auto Import
- Auto-import phim từ OPhim API (mỗi 3 phút)
- Smart Update - Chỉ cập nhật phim mới dựa trên timestamp
- Import theo thể loại, năm, hoặc custom filter

### 💾 Infrastructure
- MySQL Database với persistent storage
- Docker containerization
- FULLTEXT indexes cho search tối ưu

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Flask (Python 3.11) |
| **Database** | MySQL 8.0 (UTF8MB4) |
| **Cache** | Flask-Caching |
| **Frontend** | Vanilla JavaScript (modular) |
| **Container** | Docker + Docker Compose |
| **Import** | OPhim API + Smart Update |

## 📋 Commands Reference

### Docker Commands

```bash
# Xem logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Dừng hệ thống
docker-compose down

# Dừng và xóa database
docker-compose down -v
```

### Import Scripts (Trong Container)

```bash
# Vào trong container
docker-compose exec backend bash

# Import thủ công
python backend/scripts/ophim_import_v3.py --pages 5 --check-update

# Import theo thể loại
python backend/scripts/ophim_import_v3.py --genre phim-le --pages 3

# Import theo năm
python backend/scripts/ophim_import_v3.py --year 2024 --pages 5
```

## 🔧 Troubleshooting

### Vấn đề thường gặp

| Lỗi | Giải pháp |
|-----|-----------|
| Container không khởi động | `docker-compose down -v && docker-compose build --no-cache && docker-compose up -d` |
| Port 5000 đã dùng | Tắt service đang chạy port 5000 hoặc đổi Docker port thành `5002:5000` |
| Port 3306 đã dùng (MySQL) | Tắt local MySQL hoặc đổi Docker port thành `3308:3306` |
| Database connection error | `docker-compose logs mysql` và `docker-compose restart mysql` |
| Module not found | `docker-compose exec backend pip install -r backend/requirements.txt` |

### Thông tin cấu hình

- **Database**: MySQL 8.0 (Host: localhost:3306, DB: cgv_streaming, User: root)
- **Charset**: utf8mb4_unicode_ci  
- **Volume**: `mysql_data` (persistent data)
- **Search**: FULLTEXT indexes (hỗ trợ tiếng Việt có/không dấu)

## 👥 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo Pull Request hoặc Issue.

## 📄 License

MIT License

---

## 📧 Project Info

- **Project**: CGV Streaming Platform  
- **Version**: 3.0.0  
- **Tech Stack**: Docker, Flask, MySQL, Vanilla JS  
- **Last Updated**: December 2024

Made with ❤️ by CGV Team
