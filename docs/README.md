# 🎬 Streaming Platform v43# Full-Stack Web Application



Modern movie streaming platform với MySQL backend.A complete full-stack web application demonstrating:

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla JS with Fetch API)

## ⚡ Tính năng- **Backend**: Python Flask + Node.js Express

- **Database**: SQLite

- 🎥 **Movies & Series** - Browse phim và series với filter- **Features**: REST API, CRUD operations, Real-time statistics

- 🔍 **Smart Search** - Tìm kiếm với gợi ý realtime

- ⭐ **Favorites** - Lưu phim yêu thích## Architecture

- 📊 **Analytics** - Tracking views, likes, watch history

- 🎨 **Netflix UI** - Giao diện modern dark theme```

- 💾 **MySQL/SQLite** - Dual database support┌─────────────────────────────────────────┐

│         Frontend (HTML/CSS/JS)          │

## 🚀 Cài đặt nhanh│         http://localhost:5000           │

└──────────────┬──────────────────────────┘

### 1. Install dependencies               │

```bash       ┌───────┴────────┐

pip install -r requirements.txt       │                │

```┌──────▼──────┐  ┌─────▼──────┐

│ Flask (5000)│  │ Node (3000)│

### 2. Configure database (.env)│ Python API  │  │ Express API│

```env└──────┬──────┘  └────────────┘

USE_MYSQL=true       │

MYSQL_HOST=localhost┌──────▼──────┐

MYSQL_PORT=3306│   SQLite    │

MYSQL_USER=root│  Database   │

MYSQL_PASSWORD=your_password└─────────────┘

MYSQL_DATABASE=streaming_db```

FLASK_DEBUG=1

```## Features



### 3. Setup MySQL (first time only)### Flask Backend (Port 5000)

```bash- GET `/api/users` - Get all users

python setup_mysql.py- POST `/api/users` - Create new user

```- GET `/api/users/<id>` - Get user by ID

- DELETE `/api/users/<id>` - Delete user

### 4. Run server- SQLite database with automatic initialization

```bash

python app.py### Node.js Backend (Port 3000)

```- GET `/api/stats` - Application statistics

- POST `/api/stats/pageview` - Track page views

Server sẽ chạy tại: http://localhost:5000- POST `/api/stats/reset` - Reset statistics

- GET `/api/health` - Health check

## 📁 Cấu trúc

### Frontend Features

```- Modern responsive UI with gradient design

web/- Real-time user management (Add/Delete)

├── app.py              # Flask backend (REST API)- Live statistics from Node.js backend

├── db_manager.py       # Database connection manager- Form validation and error handling

├── setup_mysql.py      # MySQL setup & migration- Smooth animations and transitions

├── .env                # Environment config

├── requirements.txt    # Python dependencies## Prerequisites

├── database.db         # SQLite backup

└── public/### Install Python

    ├── streaming.html  # Homepage1. Download from https://www.python.org/downloads/

    ├── streaming.css   # Styles v422. Install with "Add Python to PATH" checked

    ├── streaming.js    # Frontend logic v423. Verify: `python --version`

    ├── login.html      # Auth page

    ├── movie-detail.html### Install Node.js

    └── player.html1. Download from https://nodejs.org/

```2. Choose LTS version

3. Verify: `node --version` and `npm --version`

## 🔧 Database

## Installation

**MySQL (Production):**

- Host: localhost:3306### 1. Install Python Dependencies

- Database: streaming_db

- 10 tables với indexes tối ưu```powershell

cd 'C:\Users\ADMIN\Downloads\web'

**SQLite (Backup):**pip install -r requirements.txt

- File: database.db```

- Automatic fallback nếu MySQL fail

### 2. Install Node.js Dependencies

**Switch database:**

```env```powershell

USE_MYSQL=false  # Use SQLitenpm install

USE_MYSQL=true   # Use MySQL```

```

## Running the Application

## 📋 API Endpoints

You need to run BOTH servers simultaneously (use separate terminals):

### Movies

- `GET /api/movies` - List movies (with filters & pagination)### Terminal 1: Start Flask Backend

- `GET /api/movies/<id>` - Movie detail

- `GET /api/search-suggestions` - Search autocomplete```powershell

cd 'C:\Users\ADMIN\Downloads\web'

### Userspython app.py

- `POST /api/register` - Đăng ký```

- `POST /api/login` - Đăng nhập

- `GET /api/users/<id>` - User profileFlask server will start on http://localhost:5000



### Favorites### Terminal 2: Start Node.js Backend

- `POST /api/favorites` - Toggle favorite

- `GET /api/favorites/<user_id>` - User favorites```powershell

cd 'C:\Users\ADMIN\Downloads\web'

### Watch Historynpm run start:node

- `POST /api/watch-history` - Log watch event```

- `GET /api/watch-history/<user_id>` - User history

Node.js server will start on http://localhost:3000

## 🎯 Search Features (v42)

### Open the Application

- **Realtime suggestions** - 300ms debounce

- **Keyboard navigation** - ↑↓ để chọn, Enter để xem, Esc để đóngOpen your browser and navigate to:

- **Poster thumbnails** - Preview trong dropdown```

- **Multi-field search** - Title, description, director, casthttp://localhost:5000/app.html

```

## 🛠️ Tech Stack

## File Structure

- **Backend:** Flask 3.0, PyMySQL 1.1

- **Database:** MySQL 9.4 / SQLite 3```

- **Frontend:** Vanilla JS ES6+, CSS3web/

- **Security:** Password hashing (SHA-256 + salt)├── app.py                     # Flask backend with SQLite

├── requirements.txt           # Python dependencies

## 📝 Notes├── package.json              # Node.js dependencies

├── database.db               # SQLite database (auto-created)

- SQLite reserved keyword fix: `"cast"` column wrapped in quotes├── backend/

- MySQL connection uses context manager (auto-close)│   └── node-service.js       # Node.js Express service

- Dual database support through `db_manager.py`└── public/

- Frontend versioned (CSS/JS v42 with search suggestions)    ├── app.html              # Main frontend page

    ├── app.js                # Frontend JavaScript

## 🔄 Migration    └── style.css             # Modern CSS styling

```

Migrate từ SQLite sang MySQL:

```bash## Database Schema

python setup_mysql.py

``````sql

CREATE TABLE users (

Script sẽ:    id INTEGER PRIMARY KEY AUTOINCREMENT,

1. Tạo database `streaming_db`    name TEXT NOT NULL,

2. Tạo 10 tables với proper schema    email TEXT NOT NULL UNIQUE,

3. Migrate data từ `database.db`    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

4. Show migration report);

```

## 📦 Requirements

## API Examples

```

Python 3.8+### Create User (Flask)

MySQL 8.0+ hoặc SQLite 3```bash

```curl -X POST http://localhost:5000/api/users ^

  -H "Content-Type: application/json" ^

---  -d "{\"name\":\"John Doe\",\"email\":\"john@example.com\"}"

```

**Version:** v43 (MySQL Migration)

**Last Updated:** 2024### Get Stats (Node.js)

```bash
curl http://localhost:3000/api/stats
```

## Troubleshooting

### Flask not starting
- Make sure Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check port 5000 is available

### Node.js not starting
- Make sure Node.js is installed: `node --version`
- Install dependencies: `npm install`
- Check port 3000 is available

### Frontend can't connect
- Both Flask AND Node.js servers must be running
- Check browser console for CORS errors
- Verify both servers are on correct ports

### Database errors
- Delete `database.db` and restart Flask
- Database will be recreated automatically

## Technology Stack

- **Frontend**: HTML5, CSS3 (Grid/Flexbox), Vanilla JavaScript ES6+
- **Backend 1**: Python 3.x, Flask 3.0, flask-cors
- **Backend 2**: Node.js, Express 4.x, CORS middleware
- **Database**: SQLite3 (embedded, no separate installation needed)

## License

MIT

