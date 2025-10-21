"""
Test MySQL Connection
Verify that the application can connect to MySQL database
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Load environment variables
load_dotenv()

print("="*60)
print("TESTING MYSQL CONNECTION")
print("="*60)

# Display configuration
print("\n📋 Configuration:")
print(f"   Host: {os.getenv('MYSQL_HOST', 'localhost')}")
print(f"   Port: {os.getenv('MYSQL_PORT', '3306')}")
print(f"   User: {os.getenv('MYSQL_USER', 'root')}")
print(f"   Database: {os.getenv('MYSQL_DATABASE', 'cgv_streaming')}")
print(f"   USE_MYSQL: {os.getenv('USE_MYSQL', 'false')}")

# Test connection using db_manager
try:
    from db_manager import get_db
    
    print("\n🔄 Connecting to database...")
    with get_db() as db:
        cursor = db.cursor()
        
        # Test query
        cursor.execute("SELECT DATABASE(), VERSION()")
        result = cursor.fetchone()
        
        if isinstance(result, dict):
            db_name = result.get('DATABASE()', 'Unknown')
            version = result.get('VERSION()', 'Unknown')
        else:
            db_name = result[0] if result else 'Unknown'
            version = result[1] if len(result) > 1 else 'Unknown'
        
        print("\n✅ Successfully connected to MySQL!")
        print(f"   Database: {db_name}")
        print(f"   Version: {version}")
        
        # Test table creation
        print("\n🔄 Testing table operations...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📊 Found {len(tables)} tables:")
            for table in tables:
                if isinstance(table, dict):
                    table_name = list(table.values())[0]
                else:
                    table_name = table[0]
                print(f"   - {table_name}")
        else:
            print("\n⚠️  No tables found. Run app.py to initialize database.")
        
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\n💡 Make sure pymysql is installed:")
    print("   pip install pymysql cryptography")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Check if MySQL server is running")
    print("   2. Verify credentials in .env file")
    print("   3. Make sure database 'cgv_streaming' exists")
    print("   4. Run: mysql -u root -p1732005 -e 'CREATE DATABASE IF NOT EXISTS cgv_streaming;'")

print("\n" + "="*60)
