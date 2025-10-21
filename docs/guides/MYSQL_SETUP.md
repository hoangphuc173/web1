# Hướng Dẫn Cài Đặt MySQL cho CGV Streaming

## 📋 Thông tin cấu hình

- **Database Name**: `cgv_streaming`
- **Username**: `root`
- **Password**: `1732005`
- **Host**: `localhost`
- **Port**: `3306`

## 🚀 Các bước cài đặt

### Bước 1: Cài đặt MySQL Server

Nếu chưa cài đặt MySQL, tải và cài đặt từ:
- Windows: https://dev.mysql.com/downloads/mysql/
- Mac: `brew install mysql`
- Linux: `sudo apt-get install mysql-server`

### Bước 2: Khởi động MySQL Service

**Windows:**
```powershell
net start MySQL80
```

**Mac/Linux:**
```bash
sudo mysql.server start
# hoặc
sudo systemctl start mysql
```

### Bước 3: Cài đặt Python packages

```powershell
pip install -r requirements.txt
```

Các package cần thiết:
- `pymysql==1.1.0` - MySQL connector cho Python
- `cryptography==41.0.7` - Mã hóa cho MySQL
- `python-dotenv==1.0.0` - Quản lý biến môi trường

### Bước 4: Tạo database

Chạy script khởi tạo database:

```powershell
python init_mysql.py
```

Hoặc tạo thủ công qua MySQL CLI:

```powershell
mysql -u root -p1732005 -e "CREATE DATABASE IF NOT EXISTS cgv_streaming CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Bước 5: Kiểm tra kết nối

```powershell
python test_mysql_connection.py
```

Script này sẽ:
- Kiểm tra kết nối MySQL
- Hiển thị thông tin database và version
- Liệt kê các bảng đã tạo (nếu có)

### Bước 6: Chạy ứng dụng

```powershell
python app.py
```

Ứng dụng sẽ:
- Tự động kết nối MySQL
- Tạo tất cả bảng cần thiết
- Thêm dữ liệu mẫu
- Khởi động server tại `http://localhost:5000`

## 📊 Cấu trúc Database

Hệ thống sẽ tự động tạo các bảng sau:

1. **users** - Thông tin người dùng
2. **movies** - Danh sách phim (phim lẻ & phim bộ)
3. **genres** - Thể loại phim
4. **movie_genres** - Liên kết phim-thể loại
5. **watch_history** - Lịch sử xem
6. **favorites** - Danh sách yêu thích
7. **reviews** - Đánh giá phim
8. **comments** - Bình luận
9. **subscriptions** - Gói đăng ký
10. **payments** - Thanh toán

## 🔧 Troubleshooting

### Lỗi: "Can't connect to MySQL server"

**Giải pháp:**
```powershell
# Kiểm tra MySQL đang chạy
net start MySQL80

# Hoặc khởi động lại
net stop MySQL80
net start MySQL80
```

### Lỗi: "Access denied for user 'root'"

**Giải pháp:**
1. Kiểm tra mật khẩu trong file `.env`
2. Đảm bảo mật khẩu là `1732005`
3. Hoặc đặt lại mật khẩu MySQL:

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY '1732005';
FLUSH PRIVILEGES;
```

### Lỗi: "pymysql not installed"

**Giải pháp:**
```powershell
pip install pymysql cryptography
```

### Lỗi: "Database does not exist"

**Giải pháp:**
```powershell
python init_mysql.py
```

## 🔄 So sánh SQLite vs MySQL

### Thay đổi chính:

| SQLite | MySQL |
|--------|-------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `TEXT` | `VARCHAR(255)` hoặc `TEXT` |
| `REAL` | `DECIMAL(3,1)` hoặc `FLOAT` |
| `BOOLEAN` | `TINYINT(1)` |
| `?` placeholders | `%s` placeholders (tự động chuyển đổi) |

### Lợi ích của MySQL:

✅ **Hiệu suất cao hơn** với dữ liệu lớn  
✅ **Hỗ trợ đa người dùng** tốt hơn  
✅ **Transaction** mạnh mẽ hơn  
✅ **Backup & Recovery** dễ dàng hơn  
✅ **Scalability** tốt hơn cho production  

## 📝 File cấu hình (.env)

File `.env` đã được tạo với cấu hình:

```env
USE_MYSQL=true
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1732005
MYSQL_DATABASE=cgv_streaming
```

## 🎯 Kiểm tra hoạt động

### 1. Test kết nối:
```powershell
python test_mysql_connection.py
```

### 2. Khởi tạo database:
```powershell
python init_mysql.py
```

### 3. Chạy ứng dụng:
```powershell
python app.py
```

### 4. Test API:
```powershell
curl http://localhost:5000/api/movies
```

## 💡 Lưu ý

- Đảm bảo MySQL service đang chạy trước khi start app
- Port 3306 phải available (không bị process khác sử dụng)
- Charset đã được set là `utf8mb4` để hỗ trợ tiếng Việt và emoji
- Tất cả bảng sử dụng `InnoDB` engine cho transaction support

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Chạy `python test_mysql_connection.py` để kiểm tra
2. Kiểm tra log trong console khi chạy `python app.py`
3. Xem file ARCHITECTURE.md để hiểu cấu trúc hệ thống
