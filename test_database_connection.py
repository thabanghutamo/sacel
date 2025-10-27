#!/usr/bin/env python3
"""
Test database connection for SACEL application
"""

import os
from dotenv import load_dotenv
import pymysql
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test the database connection from .env file"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    print(f"📡 Testing database connection...")
    print(f"   Database URL: {database_url.replace(database_url.split('@')[0].split('://')[1], '***:***')}")
    
    try:
        # Parse the database URL
        # Format: mysql+pymysql://user:password@host:port/database
        url = database_url.replace('mysql+pymysql://', 'mysql://')
        parsed = urlparse(url)
        
        # Extract connection parameters
        host = parsed.hostname
        port = parsed.port or 3306
        user = parsed.username
        password = parsed.password
        database = parsed.path.lstrip('/')
        
        print(f"\n📊 Connection Details:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   User: {user}")
        print(f"   Database: {database}")
        
        # Attempt connection
        print(f"\n🔌 Connecting to database...")
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10
        )
        
        print("✅ Database connection successful!")
        
        # Test a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   MySQL Version: {version[0]}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   Tables found: {len(tables)}")
            if tables:
                print(f"   Table names: {[table[0] for table in tables]}")
        
        connection.close()
        print("\n✅ All database tests passed!")
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"\n❌ Database connection failed!")
        print(f"   Error code: {e.args[0]}")
        print(f"   Error message: {e.args[1]}")
        
        if e.args[0] == 1045:
            print("\n💡 Access denied - Check your credentials:")
            print("   - Verify username and password in .env file")
            print("   - Make sure the database user has proper permissions")
        elif e.args[0] == 2003:
            print("\n💡 Cannot connect to database server:")
            print("   - Check if the host and port are correct")
            print("   - Verify network connectivity")
            print("   - Check firewall settings")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}")
        print(f"   {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("SACEL Database Connection Test")
    print("=" * 60)
    
    success = test_database_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Database is ready for use!")
    else:
        print("❌ Please fix database connection issues before running the app")
    print("=" * 60)
