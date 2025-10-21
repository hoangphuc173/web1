# 🔄 Smart Update - Cập nhật thông minh

## 📋 Tính năng mới

Hệ thống giờ có thể **so sánh thời gian cập nhật** giữa OPhim API và database để:
- ✅ Chỉ import phim **thực sự mới**
- ✅ **Update** phim đã có nếu có bản cập nhật mới hơn
- ✅ **Bỏ qua** phim đã up-to-date, tiết kiệm thời gian
- ✅ Tự động **xóa và thêm lại episodes** khi update

## 🚀 Cách sử dụng

### 1. Auto Import (Tự động, mặc định BẬT smart update)

```powershell
# Scheduler tự động - Đã tích hợp smart update
python ophim_import_v3.py --auto

# Chạy ngay - Đã tích hợp smart update
python ophim_import_v3.py --run-now
```

### 2. Manual Import với Smart Update

```powershell
# Import với kiểm tra update
python ophim_import_v3.py --pages 5 --check-update

# Import theo thể loại với kiểm tra
python ophim_import_v3.py --genre action --pages 3 --check-update

# Import theo năm với kiểm tra
python ophim_import_v3.py --year 2024 --pages 2 --check-update
```

### 3. Manual Import không kiểm tra (Force import)

```powershell
# Import bình thường (không kiểm tra, có thể trùng)
python ophim_import_v3.py --pages 5

# Import phim cụ thể
python ophim_import_v3.py --slug ten-phim-slug
```

## 🔍 Cách hoạt động

### Khi import một phim:

1. **Lấy thông tin từ OPhim API**
   - Thời gian cập nhật: `modified.time` (ví dụ: "2025-10-19 15:30:00")

2. **Kiểm tra trong database**
   - Tìm phim theo `title` hoặc `slug`
   - Lấy thời gian update: `updated_at`

3. **So sánh thời gian**
   ```
   Nếu OPhim time > DB time:
       → UPDATE phim (ghi đè thông tin mới)
       → XÓA episodes cũ và thêm episodes mới
   
   Nếu OPhim time <= DB time:
       → BỎ QUA (phim đã mới nhất)
   
   Nếu không tìm thấy trong DB:
       → INSERT phim mới
   ```

## 📊 Ví dụ Output

### Với Smart Update:

```
======================================================================
🎬 OPHIM IMPORTER V3 - Full Episode Support
🔄 Smart Update Mode: Only import new/updated movies
======================================================================

📄 Processing page 1/3
----------------------------------------------------------------------

[1/20] 
🎬 Processing: Người Vận Chuyển 5
  📅 Modified: 2025-10-19 14:30:00
  ✅ Movie already up-to-date (ID: 123)

[2/20] 
🎬 Processing: John Wick 4
  📅 Modified: 2025-10-19 16:45:00
  🔄 Movie exists but has updates (OPhim: 2025-10-19 16:45:00 > DB: 2025-10-18 10:20:00)
  ➡️ Updating movie ID: 456
  ✅ Updated movie ID: 456
  🗑️ Cleared old episodes
  ✅ Inserted 25 episodes

[3/20] 
🎬 Processing: Spider-Man: No Way Home Extended
  📅 Modified: 2025-10-19 18:00:00
  ✅ Inserted movie ID: 789

======================================================================
🎉 Import completed! New/Updated: 45, Skipped: 15
======================================================================
```

### Không có Smart Update (Force):

```
======================================================================
🎬 OPHIM IMPORTER V3 - Full Episode Support
======================================================================

[1/20] 
🎬 Processing: Người Vận Chuyển 5
  ⚠️ Movie already exists (ID: 123)

[2/20] 
🎬 Processing: John Wick 4
  ⚠️ Movie already exists (ID: 456)
...
```

## ⚙️ Cấu hình

### Auto Import đã tích hợp sẵn Smart Update

Mở `ophim_import_v3.py`, dòng 316:

```python
# Mặc định đã BẬT check_update_time=True
total = self.importer.import_batch(num_pages=3, year=None, check_update_time=True)
```

Nếu muốn TẮT (không khuyến nghị):
```python
total = self.importer.import_batch(num_pages=3, year=None, check_update_time=False)
```

## 📈 Lợi ích

| Tính năng | Không Smart Update | Có Smart Update |
|-----------|-------------------|-----------------|
| Thời gian import | ~10 phút | ~2-3 phút |
| Phim trùng | Có (skip) | Không (update) |
| Phim có update mới | Bỏ lỡ | Tự động update |
| Episodes mới | Không update | Tự động update |
| Hiệu suất | Chậm | Nhanh ⚡ |

## ❓ FAQ

**Q: Smart Update có làm chậm quá trình import không?**
A: Không, thậm chí còn nhanh hơn vì bỏ qua nhiều phim không cần xử lý.

**Q: Nếu phim có thêm tập mới thì sao?**
A: Smart Update sẽ phát hiện thời gian cập nhật mới hơn và tự động update toàn bộ episodes.

**Q: Có thể tắt Smart Update không?**
A: Có, bỏ flag `--check-update` khi chạy manual, hoặc sửa code trong `daily_import_job()`.

**Q: Smart Update có hoạt động với phim lẻ (single movie) không?**
A: Có, update cả thông tin phim và video URL.

**Q: Làm sao biết có bao nhiêu phim được update?**
A: Xem output cuối cùng: "New/Updated: X, Skipped: Y"

## 🔧 Troubleshooting

### Lỗi: Could not compare timestamps

**Nguyên nhân:** Format thời gian không đúng hoặc thiếu dữ liệu

**Giải pháp:** Script sẽ tự động fallback về chế độ kiểm tra bình thường

### Phim không được update dù có bản mới

**Kiểm tra:**
1. Thời gian trong DB: `SELECT updated_at FROM movies WHERE title = 'Tên phim'`
2. Thời gian từ API: Xem log output `📅 Modified: ...`
3. So sánh xem OPhim time có lớn hơn DB time không

### Database lỗi khi update

**Nguyên nhân:** Schema database không có cột `updated_at`

**Giải pháp:** 
```sql
ALTER TABLE movies ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
```

---

**Version**: 3.1
**Last Updated**: 2025-10-19
**Feature**: Smart Update with Timestamp Comparison
