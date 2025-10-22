#!/usr/bin/env python3
"""
Check and Create FULLTEXT Indexes for Search Optimization
Run this script to ensure FULLTEXT indexes exist on the movies table
"""

import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', '.env')
load_dotenv(env_path)

def get_db_connection():
    """Get MySQL database connection"""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'mysql'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'root'),
        database=os.getenv('DB_NAME', 'cgv_streaming'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def check_fulltext_indexes(cursor):
    """Check if FULLTEXT indexes already exist"""
    cursor.execute("""
        SELECT INDEX_NAME, COLUMN_NAME
        FROM information_schema.STATISTICS 
        WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'movies' 
            AND INDEX_TYPE = 'FULLTEXT'
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
    """)
    
    indexes = cursor.fetchall()
    existing = {}
    
    for idx in indexes:
        idx_name = idx['INDEX_NAME']
        col_name = idx['COLUMN_NAME']
        if idx_name not in existing:
            existing[idx_name] = []
        existing[idx_name].append(col_name)
    
    return existing

def create_fulltext_indexes():
    """Create FULLTEXT indexes on movies table for optimized search"""
    
    print("🔍 FULLTEXT Index Setup for Search Optimization\n")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check existing indexes
        print("\n📋 Checking existing FULLTEXT indexes...")
        existing = check_fulltext_indexes(cursor)
        
        if existing:
            print("✅ Found existing FULLTEXT indexes:")
            for idx_name, columns in existing.items():
                print(f"   - {idx_name}: {', '.join(columns)}")
        else:
            print("ℹ️  No FULLTEXT indexes found")
        
        # Define FULLTEXT indexes to create
        fulltext_indexes = [
            {
                'name': 'ft_title',
                'columns': ['title'],
                'sql': 'CREATE FULLTEXT INDEX ft_title ON movies(title)'
            },
            {
                'name': 'ft_original_title',
                'columns': ['original_title'],
                'sql': 'CREATE FULLTEXT INDEX ft_original_title ON movies(original_title)'
            },
            {
                'name': 'ft_description',
                'columns': ['description'],
                'sql': 'CREATE FULLTEXT INDEX ft_description ON movies(description)'
            },
            {
                'name': 'ft_search_all',
                'columns': ['title', 'original_title', 'description'],
                'sql': 'CREATE FULLTEXT INDEX ft_search_all ON movies(title, original_title, description)'
            }
        ]
        
        print("\n🔨 Creating FULLTEXT indexes...")
        created_count = 0
        skipped_count = 0
        
        for idx_info in fulltext_indexes:
            idx_name = idx_info['name']
            
            # Check if index already exists
            if idx_name in existing:
                print(f"   ⏭️  Skipped: {idx_name} (already exists)")
                skipped_count += 1
                continue
            
            try:
                cursor.execute(idx_info['sql'])
                print(f"   ✅ Created: {idx_name} on {', '.join(idx_info['columns'])}")
                created_count += 1
            except pymysql.err.OperationalError as e:
                if "Duplicate key name" in str(e):
                    print(f"   ⏭️  Skipped: {idx_name} (already exists)")
                    skipped_count += 1
                else:
                    print(f"   ❌ Failed: {idx_name} - {str(e)}")
        
        # Optimize table after creating indexes
        if created_count > 0:
            print("\n🔧 Optimizing table to rebuild indexes...")
            cursor.execute("OPTIMIZE TABLE movies")
            print("   ✅ Table optimized")
        
        conn.commit()
        
        # Verify final state
        print("\n📊 Final FULLTEXT index status:")
        final_indexes = check_fulltext_indexes(cursor)
        
        if final_indexes:
            for idx_name, columns in final_indexes.items():
                print(f"   ✅ {idx_name}: {', '.join(columns)}")
        
        print("\n" + "=" * 60)
        print(f"✅ Setup complete!")
        print(f"   - Created: {created_count} indexes")
        print(f"   - Skipped: {skipped_count} indexes (already existed)")
        print(f"   - Total FULLTEXT indexes: {len(final_indexes)}")
        print("\n🚀 Search optimization is ready!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    create_fulltext_indexes()
