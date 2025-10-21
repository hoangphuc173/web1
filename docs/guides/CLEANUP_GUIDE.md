# 🧹 Cleanup Manager - Hướng dẫn sử dụng

Công cụ tự động dọn dẹp các file test và file tạm trong workspace.

## 📋 Mục đích

- Tự động phát hiện và xóa các file test
- Theo dõi lịch sử cleanup
- Xóa file cũ theo thời gian
- Giữ workspace sạch sẽ

## 🎯 Các file được tự động xóa

### Patterns:
- `test_*.py` - File test
- `check_*.py` - File kiểm tra
- `migrate_*.py` - File migration
- `temp_*.py` - File tạm
- `debug_*.py` - File debug
- `*_test.py` - File test (suffix)
- `*_check.py` - File check (suffix)
- `*.tmp` - File temporary
- `*.temp` - File temp

### Các file KHÔNG bị xóa:
- `test_api.py` - File test chính
- `requirements.txt` - Dependencies
- `setup.py` - Setup file
- Files trong `.venv/`
- Files trong `node_modules/`

## 🚀 Cách sử dụng

### 1. Xem trạng thái
```powershell
python cleanup_manager.py status
```

Output:
```
============================================================
FILE CLEANUP STATUS
============================================================

📝 Tracked Test Files: 5
  - check_db.py (1024 bytes)
  - check_schema.py (2048 bytes)
  ... and 3 more

🗑️  Deleted Files: 3
  Total space freed: 5,120 bytes

🕐 Last Cleanup: 2025-10-14T02:30:00

📂 Current Test Files: 2
  - temp_script.py (512 bytes)
  - debug_test.py (256 bytes)
============================================================
```

### 2. Dry Run (Xem trước)
```powershell
python cleanup_manager.py dry-run
```

Hiển thị file sẽ bị xóa KHÔNG thực sự xóa:
```
DRY RUN: Found 2 test files:
  - temp_script.py (512 bytes)
  - debug_test.py (256 bytes)
```

### 3. Cleanup thực sự
```powershell
python cleanup_manager.py cleanup
```

Xóa tất cả file test:
```
Found 2 test files:
  - temp_script.py (512 bytes)
    ✓ Deleted
  - debug_test.py (256 bytes)
    ✓ Deleted

✓ Cleaned up 2 files (768 bytes)
```

### 4. Auto Cleanup (Interactive)
```powershell
python cleanup_manager.py auto
```

Tự động cleanup với xác nhận:
```
⚠️  Found 2 test files to clean up:
  - temp_script.py
  - debug_test.py

Cleanup? (y/n):
```

### 5. Xóa file cũ
```powershell
# Xóa file cũ hơn 24 giờ
python cleanup_manager.py old 24

# Xóa file cũ hơn 1 giờ
python cleanup_manager.py old 1

# Xóa file cũ hơn 7 ngày (168 giờ)
python cleanup_manager.py old 168
```

## 📊 Cleanup Log

File `cleanup_log.json` lưu trữ:

```json
{
  "created": [
    {
      "file": "temp_script.py",
      "created_at": "2025-10-14T02:00:00",
      "size": 512
    }
  ],
  "deleted": [
    {
      "file": "temp_script.py",
      "deleted_at": "2025-10-14T02:30:00",
      "size": 512
    }
  ],
  "last_cleanup": "2025-10-14T02:30:00"
}
```

## 🔧 Tích hợp vào workflow

### Option 1: Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/sh
python cleanup_manager.py auto
```

### Option 2: Scheduled Task (Windows)
```powershell
# Chạy mỗi ngày lúc 3 giờ sáng
$action = New-ScheduledTaskAction -Execute 'python' -Argument 'cleanup_manager.py cleanup'
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Cleanup Test Files"
```

### Option 3: Cron Job (Linux/Mac)
```bash
# Chạy mỗi ngày lúc 3 giờ sáng
0 3 * * * cd /path/to/web && python cleanup_manager.py cleanup
```

## 🎨 Customization

### Thêm pattern mới:
```python
# Trong cleanup_manager.py
self.test_patterns = [
    'test_*.py',
    'check_*.py',
    'your_pattern_*.py',  # ← Thêm pattern của bạn
]
```

### Exclude files:
```python
# Trong cleanup_manager.py
exclude_files = [
    'test_api.py',
    'requirements.txt',
    'important_test.py',  # ← Thêm file không muốn xóa
]
```

## ⚠️ Lưu ý

1. **Backup quan trọng**: Luôn backup trước khi cleanup
2. **Kiểm tra dry-run**: Chạy dry-run trước khi cleanup thật
3. **Review log**: Xem cleanup_log.json sau khi cleanup
4. **Git commit**: Commit code quan trọng trước khi cleanup

## 🐛 Troubleshooting

### Lỗi: Permission denied
```powershell
# Chạy với quyền admin
python cleanup_manager.py cleanup
```

### Lỗi: File đang được sử dụng
```powershell
# Đóng tất cả editor/IDE
# Dừng server đang chạy
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
python cleanup_manager.py cleanup
```

### Lỗi: JSON decode error
```powershell
# Xóa log file bị corrupt
Remove-Item cleanup_log.json
python cleanup_manager.py status
```

## 📚 API Reference

### FileCleanupManager Class

```python
from cleanup_manager import FileCleanupManager

# Khởi tạo
manager = FileCleanupManager(workspace_dir='.')

# Đăng ký file test
manager.register_test_file('temp_test.py')

# Tìm file test
files = manager.find_test_files()

# Cleanup
cleaned = manager.cleanup_test_files(dry_run=False)

# Xóa file cũ
old_files = manager.cleanup_old_files(max_age_hours=24)

# Hiển thị status
manager.show_status()

# Lấy thông tin
info = manager.log
```

## 💡 Tips & Tricks

1. **Chạy cleanup trước khi commit**:
   ```powershell
   python cleanup_manager.py cleanup; git add .; git commit -m "message"
   ```

2. **Tạo alias**:
   ```powershell
   # PowerShell profile
   function cleanup { python cleanup_manager.py cleanup }
   ```

3. **Schedule weekly cleanup**:
   ```powershell
   # Mỗi Chủ nhật lúc 2 giờ sáng
   python cleanup_manager.py old 168
   ```

## 🎯 Best Practices

1. ✅ Chạy `status` thường xuyên để theo dõi
2. ✅ Dùng `dry-run` trước khi `cleanup`
3. ✅ Review `cleanup_log.json` sau cleanup
4. ✅ Backup trước khi cleanup lần đầu
5. ✅ Thêm vào `.gitignore`: `cleanup_log.json`

## 📞 Support

Nếu có vấn đề:
1. Check log file: `cleanup_log.json`
2. Run với verbose: `python cleanup_manager.py status`
3. Manual cleanup: `Remove-Item temp_*.py`

---

**Version:** 1.0.0  
**Last Updated:** 14 Tháng 10, 2025
