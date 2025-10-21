"""
Database Manager - MySQL Connection & Setup
Manages MySQL database connection and operations
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from config/.env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', '.env')
load_dotenv(env_path)

# Force MySQL usage
USE_MYSQL = True

if USE_MYSQL:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        print("⚠️  PyMySQL not installed. Run: pip install pymysql cryptography")
        USE_MYSQL = False


class MySQLCursorWrapper:
    """Wrapper to convert ? placeholders to MySQL %s placeholders"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute(self, query, params=None):
        """Execute query with automatic placeholder conversion"""
        if params:
            # Convert ? to %s for MySQL
            query = query.replace('?', '%s')
        return self.cursor.execute(query, params)
    
    def executemany(self, query, params_list):
        """Execute many queries with placeholder conversion"""
        query = query.replace('?', '%s')
        return self.cursor.executemany(query, params_list)
    
    def fetchone(self):
        return self.cursor.fetchone()
    
    def fetchall(self):
        return self.cursor.fetchall()
    
    def fetchmany(self, size=None):
        return self.cursor.fetchmany(size)
    
    @property
    def lastrowid(self):
        return self.cursor.lastrowid
    
    @property
    def rowcount(self):
        return self.cursor.rowcount
    
    def close(self):
        return self.cursor.close()
    
    def __iter__(self):
        return iter(self.cursor)


class DatabaseConnection:
    """MySQL Database connection wrapper"""
    
    def __init__(self):
        self.use_mysql = True
        self.connection = None
        self._connect_mysql()
    
    def _connect_mysql(self):
        """Connect to MySQL database"""
        try:
            import pymysql
            
            self.connection = pymysql.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'cgv_streaming'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            print("[OK] Connected to MySQL database")
        except ImportError:
            print("[ERROR] PyMySQL not installed!")
            print("[HINT] Install with: pip install pymysql cryptography")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] MySQL connection failed: {e}")
            print("[HINT] Check your MySQL server and credentials in config/.env")
            sys.exit(1)
    
    def cursor(self):
        """Get database cursor with placeholder conversion support"""
        return MySQLCursorWrapper(self.connection.cursor())
    
    def commit(self):
        """Commit transaction"""
        self.connection.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.connection.rollback()
    
    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db():
    """
    Get MySQL database connection
    Returns MySQL connection
    """
    return DatabaseConnection()


def convert_placeholder(query):
    """
    Convert ? placeholders to %s for MySQL
    MySQL uses %s for parameter placeholders
    """
    # Always convert ? to %s for MySQL
    return query.replace('?', '%s')


# Example usage:
if __name__ == '__main__':
    print("="*60)
    print("MYSQL DATABASE CONNECTION TEST")
    print("="*60)
    
    with get_db() as db:
        cursor = db.cursor()
        
        # Test query for MySQL
        print("\n✓ Using MySQL")
        cursor.execute("SELECT VERSION()")
        
        result = cursor.fetchone()
        print(f"Database version: {result}")
    
    print("\n✅ Connection test successful!")


# ============================================================
# MYSQL DATABASE SETUP & MANAGEMENT
# ============================================================

def create_mysql_database():
    """
    Create MySQL database if it doesn't exist
    Returns: (success: bool, message: str)
    """
    try:
        import pymysql
        
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        db_name = os.getenv('MYSQL_DATABASE', 'cgv_streaming')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        cursor.close()
        connection.close()
        
        return True, f"Database '{db_name}' created successfully"
        
    except Exception as e:
        return False, f"Failed to create database: {e}"


def drop_mysql_database():
    """
    Drop MySQL database (use with caution!)
    Returns: (success: bool, message: str)
    """
    if not USE_MYSQL:
        return False, "MySQL is not enabled"
    
    try:
        import pymysql
        
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        db_name = os.getenv('MYSQL_DATABASE', 'cgv_streaming')
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        
        cursor.close()
        connection.close()
        
        return True, f"Database '{db_name}' dropped successfully"
        
    except Exception as e:
        return False, f"Failed to drop database: {e}"


def reset_mysql_database():
    """
    Drop and recreate MySQL database
    Returns: (success: bool, message: str)
    """
    success, msg = drop_mysql_database()
    if not success:
        return False, msg
    
    success, msg = create_mysql_database()
    return success, msg


def get_database_info():
    """
    Get MySQL database information (version, tables, counts)
    Returns: dict with database info
    """
    try:
        with get_db() as db:
            cursor = db.cursor()
            
            info = {
                'type': 'MySQL',
                'version': None,
                'database': os.getenv('MYSQL_DATABASE', 'cgv_streaming'),
                'tables': [],
                'table_counts': {}
            }
            
            # Get MySQL version
            cursor.execute("SELECT VERSION()")
            result = cursor.fetchone()
            info['version'] = list(result.values())[0] if isinstance(result, dict) else result[0]
            
            # Get tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for table in tables:
                table_name = list(table.values())[0] if isinstance(table, dict) else table[0]
                info['tables'].append(table_name)
                
                # Get count for each table
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    result = cursor.fetchone()
                    count = list(result.values())[0] if isinstance(result, dict) else result[0]
                    info['table_counts'][table_name] = count
                except Exception:
                    info['table_counts'][table_name] = 0
            
            return info
            
    except Exception as e:
        return {'error': str(e)}


def test_connection():
    """
    Test database connection and display information
    """
    print("="*60)
    print("DATABASE CONNECTION TEST")
    print("="*60)
    
    print("\n📋 Configuration:")
    if USE_MYSQL:
        print("   Type: MySQL")
        print(f"   Host: {os.getenv('MYSQL_HOST', 'localhost')}")
        print(f"   Port: {os.getenv('MYSQL_PORT', '3306')}")
        print(f"   User: {os.getenv('MYSQL_USER', 'root')}")
        print(f"   Database: {os.getenv('MYSQL_DATABASE', 'cgv_streaming')}")
    
    try:
        info = get_database_info()
        
        if 'error' in info:
            print(f"\n❌ Connection failed: {info['error']}")
            return False
        
        print("\n✅ Connected successfully!")
        print(f"   Version: {info['version']}")
        print(f"\n📊 Tables ({len(info['tables'])}):")
        
        for table in sorted(info['tables']):
            count = info['table_counts'].get(table, 0)
            print(f"   - {table}: {count} rows")
        
        print("\n" + "="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        if USE_MYSQL:
            print("   1. Check if MySQL server is running")
            print("   2. Verify credentials in .env file")
            print("   3. Run: python db_manager.py --setup")
        print("\n" + "="*60)
        return False


def setup_database():
    """
    Setup MySQL database (create database)
    """
    print("="*60)
    print("MYSQL DATABASE SETUP")
    print("="*60)
    
    if not USE_MYSQL:
        print("\n⚠️  MySQL is not enabled!")
        print("Set USE_MYSQL=true in .env file")
        return False
    
    print(f"\n🔄 Creating database '{os.getenv('MYSQL_DATABASE', 'cgv_streaming')}'...")
    success, message = create_mysql_database()
    
    if success:
        print(f"✅ {message}")
        print("\n💡 Next steps:")
        print("   1. Run: python app.py")
        print("   2. Tables will be created automatically")
        print("   3. Sample data will be inserted")
        return True
    else:
        print(f"❌ {message}")
        return False


def reset_database():
    """
    Reset MySQL database (drop and recreate)
    """
    print("="*60)
    print("RESET MYSQL DATABASE")
    print("="*60)
    print("\n⚠️  WARNING: This will delete all data!")
    
    if not USE_MYSQL:
        print("\n⚠️  MySQL is not enabled!")
        return False
    
    response = input("\nAre you sure? Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("❌ Operation cancelled")
        return False
    
    print("\n🔄 Resetting database...")
    success, message = reset_mysql_database()
    
    if success:
        print(f"✅ {message}")
        print("\n💡 Run: python app.py to reinitialize")
        return True
    else:
        print(f"❌ {message}")
        return False


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == '--test' or command == '-t':
            test_connection()
            
        elif command == '--setup' or command == '-s':
            setup_database()
            
        elif command == '--reset' or command == '-r':
            reset_database()
            
        elif command == '--info' or command == '-i':
            info = get_database_info()
            print("="*60)
            print("DATABASE INFORMATION")
            print("="*60)
            print(f"\nType: {info.get('type')}")
            print(f"Version: {info.get('version')}")
            print(f"Database: {info.get('database')}")
            print(f"\nTables: {len(info.get('tables', []))}")
            for table in sorted(info.get('tables', [])):
                count = info.get('table_counts', {}).get(table, 0)
                print(f"  - {table}: {count} rows")
            
        elif command == '--help' or command == '-h':
            print("="*60)
            print("DATABASE MANAGER - HELP")
            print("="*60)
            print("\nUsage: python db_manager.py [command]")
            print("\nCommands:")
            print("  --test,  -t    Test database connection")
            print("  --setup, -s    Setup MySQL database")
            print("  --reset, -r    Reset MySQL database (drops and recreates)")
            print("  --info,  -i    Show database information")
            print("  --help,  -h    Show this help message")
            print("\nExamples:")
            print("  python db_manager.py --test")
            print("  python db_manager.py --setup")
            print("  python db_manager.py --info")
            
        else:
            print(f"Unknown command: {command}")
            print("Run: python db_manager.py --help")
    else:
        # Default: run connection test
        test_connection()
