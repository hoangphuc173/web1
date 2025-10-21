# 🎬 CGV Streaming Platform

Nền tảng xem phim trực tuyến với tính năng tự động import phim từ OPhim API.

## 📁 Cấu trúc Project

```
web1/
├── backend/                 # Backend API & Services
│   ├── app.py              # Flask application chính
│   ├── db_manager.py       # Database manager
│   ├── requirements.txt    # Python dependencies
│   ├── scripts/            # Import & utility scripts
│   │   ├── ophim_import_v3.py
│   │   ├── cleanup_manager.py
│   │   ├── clear_db.py
│   │   ├── verify_data.py
│   │   └── test_mysql_connection.py
│   ├── start_auto_import.bat
│   └── run_import_now.bat
│
├── frontend/               # Frontend files
│   └── public/
│       ├── pages/         # HTML pages
│       ├── css/           # Stylesheets
│       └── js/            # JavaScript files
│           └── core/      # Core modules
│
├── data/                   # Database & data files
│   ├── databases/         # SQLite databases
│   ├── logs/              # Log files
│   └── cache/             # Cache files
│
├── docs/                   # Documentation
│   ├── README.md
│   ├── ARCHITECTURE.md
│   └── guides/            # User guides
│
├── config/                 # Configuration files
│   └── .env               # Environment variables
│
├── tests/                  # Test files
│
└── run_server.bat          # Start server script
```

## 🚀 Cài đặt

### 1. Cài đặt dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Tạo file `config/.env`:

```env
# Database Configuration
USE_MYSQL=false
DATABASE_URL=sqlite:///../data/databases/cgv_streaming.db

# MySQL Configuration (nếu sử dụng)
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=cgv_streaming
```

### 3. Khởi động server

```bash
# Từ thư mục gốc
run_server.bat

# Hoặc
cd backend
python app.py
```

Server sẽ chạy tại: `http://localhost:5000`

## 📚 Tính năng

### ✅ Đã hoàn thành

- ✅ Hệ thống xem phim với player tích hợp
- ✅ Đăng nhập / Đăng ký người dùng
- ✅ Yêu thích & Lịch sử xem
- ✅ Tìm kiếm phim
- ✅ Phân loại phim (Phim lẻ, Phim bộ, Thể loại)
- ✅ Auto-import phim từ OPhim API (2 lần/ngày: 12:00 & 00:00)
- ✅ Smart Update - Chỉ cập nhật phim mới dựa trên timestamp
- ✅ Hỗ trợ cả MySQL và SQLite

### 🔄 Import Phim

#### Tự động (Auto Import)

```bash
cd backend
start_auto_import.bat
```

Lịch trình: 12:00 (trưa) và 00:00 (nửa đêm) hằng ngày

#### Thủ công (Manual Import)

```bash
cd backend
run_import_now.bat

# Hoặc với tùy chọn
cd backend
python scripts\ophim_import_v3.py --pages 5 --check-update
```

## 📖 Tài liệu

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Auto Import Guide](docs/guides/AUTO_IMPORT_GUIDE.md)
- [Smart Update Guide](docs/guides/SMART_UPDATE_GUIDE.md)
- [Database Manager Guide](docs/guides/DB_MANAGER_GUIDE.md)
- [MySQL Setup](docs/guides/MYSQL_SETUP.md)
- [Performance Optimization](docs/guides/PERFORMANCE_OPTIMIZATION.md)

## 🛠️ Công nghệ sử dụng

### Backend
- **Flask** - Python web framework
- **SQLite / MySQL** - Database
- **Requests** - HTTP client
- **Schedule** - Task scheduler
- **python-dotenv** - Environment management

### Frontend
- **Vanilla JavaScript** - No frameworks
- **Modular Architecture** - Core modules system
- **Responsive Design** - Mobile-friendly

## 📝 Scripts hữu ích

### Backend Scripts

```bash
# Xóa toàn bộ database
cd backend\scripts
python clear_db.py

# Kiểm tra dữ liệu
python verify_data.py

# Test MySQL connection
python test_mysql_connection.py
```

### Import Scripts

```bash
# Import theo thể loại
python scripts\ophim_import_v3.py --genre phim-le --pages 3

# Import theo năm
python scripts\ophim_import_v3.py --year 2024 --pages 5

# Import với Smart Update
python scripts\ophim_import_v3.py --check-update --pages 10
```

## 🔧 Troubleshooting

### Lỗi import module

Nếu gặp lỗi `ModuleNotFoundError: No module named 'db_manager'`:

```bash
cd backend
pip install -r requirements.txt
```

### Database không tìm thấy

Database sẽ tự động được tạo tại `data/databases/cgv_streaming.db` khi chạy server lần đầu.

### Port 5000 đã được sử dụng

Sửa trong `backend/app.py`, dòng cuối:

```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Đổi sang port khác
```

## 👥 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo Pull Request hoặc Issue.

## 📄 License

MIT License

## 📧 Liên hệ

- **Project**: CGV Streaming Platform
- **Version**: 3.0.0
- **Last Updated**: October 2025

---

Made with ❤️ by CGV Team
