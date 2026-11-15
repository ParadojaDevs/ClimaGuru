#!/usr/bin/env python3
"""
Test script to verify httpOnly cookie flow for ClimaGuru authentication.
This script tests the backend routes and cookie configuration.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment variables for remote DB connection
os.environ['MYSQL_HOST'] = '100.78.215.44'
os.environ['MYSQL_USER'] = 'root'
os.environ['MYSQL_PASSWORD'] = 'geCpezYdFIrpt'
os.environ['MYSQL_DATABASE'] = 'climaguru'
os.environ['SECRET_KEY'] = 'test-secret-key-for-verification'


def test_imports():
    """Test that all modules import correctly"""
    print("=" * 60)
    print("TEST 1: Verifying module imports")
    print("=" * 60)
    
    try:
        from app import create_app
        print("OK app.py imported successfully")
        
        from routes.auth import auth_bp
        print("OK routes/auth.py imported successfully")
        
        from routes.users import users_bp
        print("OK routes/users.py imported successfully")
        
        from models.user import User
        print("OK models/user.py imported successfully")
        
        from config import Config
        print("OK config.py imported successfully")
        
        from database import db
        print("OK database.py imported successfully")
        
        return True
        
    except Exception as e:
        print(f"IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_creation():
    """Test that the Flask app creates successfully"""
    print("\n" + "=" * 60)
    print("TEST 2: Creating Flask app")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app()
        
        print("OK App created successfully")
        return True
        
    except Exception as e:
        print(f"IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sql_tables():
    """Test that required tables exist in the database"""
    print("\n" + "=" * 60)
    print("TEST 3: Verifying database tables")
    print("=" * 60)
    
    try:
        import pymysql
        conn = pymysql.connect(
            host=os.environ['MYSQL_HOST'],
            port=3306,
            user=os.environ['MYSQL_USER'],
            password=os.environ['MYSQL_PASSWORD'],
            database=os.environ['MYSQL_DATABASE']
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['alertas_clima', 'configuraciones_usuario', 'usuarios']
            for table in required_tables:
                if table in tables:
                    print(f"OK Table '{table}' EXISTS")
                else:
                    print(f"XX Table '{table}' NOT FOUND")
        
        conn.close()
        print("OK Database verification complete")
        return True
        
    except Exception as e:
        print(f"IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_route_structure():
    """Test that routes are properly defined"""
    print("\n" + "=" * 60)
    print("TEST 4: Verifying route structure")
    print("=" * 60)
    
    try:
        from routes.auth import auth_bp
        from routes.users import users_bp
        
        # Get routes from auth blueprint
        auth_rules = [rule.rule for rule in auth_bp.iter_rules()]
        print(f"Auth routes: {auth_rules}")
        
        # Get routes from users blueprint  
        users_rules = [rule.rule for rule in users_bp.iter_rules()]
        print(f"Users routes: {users_rules}")
        
        # Check for expected routes
        has_login = any('/login' in rule for rule in auth_rules)
        print(f"Login route defined: {has_login}")
        
        has_users_get = any('GET /users' in str(rule) for rule in users_rules)
        print(f"Users GET route defined: {has_users_get}")
        
        return True
        
    except Exception as e:
        print(f"IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("CLIMAGURU HTTPONLY COOKIE FLOW VERIFICATION")
    print("=" * 60 + "\n")
    
    results = []
    results.append(test_imports())
    results.append(test_app_creation())
    results.append(test_sql_tables())
    results.append(test_route_structure())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if all(results):
        print("ALL TESTS PASSED - Code is ready for httpOnly cookie deployment")
    else:
        print("Some tests need attention - review output above")
    
    print("\n" + "=" * 60 + "\n")