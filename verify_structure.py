#!/usr/bin/env python3
"""
SANCHAY IAS - Cleanup Verification Script
Checks if all files are properly organized
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def verify_structure():
    """Verify the project structure is correct"""
    
    print("=" * 70)
    print("SANCHAY IAS - STRUCTURE VERIFICATION")
    print("=" * 70)
    
    required_folders = [
        'backend',
        'frontend',
        'tests',
        'scripts',
        'data',
        'config',
        'docs',
    ]
    
    required_files = {
        'backend': ['api_server.py', 'sanchay_db.py', 'ingestion_engine.py', '__init__.py'],
        'frontend': ['app.js', 'config.js'],
        'docs': ['API_REFERENCE.md', 'DEPLOYMENT.md'],
        'root': ['.env.example', '.gitignore', 'requirements.txt', 'README.md'],
        'scripts': ['init_local_db.py'],
    }
    
    # Check folders
    print("\n📁 FOLDER STRUCTURE")
    print("-" * 70)
    all_folders_exist = True
    for folder in required_folders:
        path = PROJECT_ROOT / folder
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {folder}/")
        if not exists:
            all_folders_exist = False
    
    # Check files
    print("\n📄 REQUIRED FILES")
    print("-" * 70)
    all_files_exist = True
    for location, files in required_files.items():
        print(f"\n  {location}/")
        for filename in files:
            if location == 'root':
                path = PROJECT_ROOT / filename
            else:
                path = PROJECT_ROOT / location / filename
            
            exists = path.exists()
            status = "✓" if exists else "✗"
            print(f"    {status} {filename}")
            if not exists:
                all_files_exist = False
    
    # Check data folder is empty (ready for database)
    print("\n💾 DATA FOLDER")
    print("-" * 70)
    data_path = PROJECT_ROOT / 'data'
    if data_path.exists():
        files_in_data = list(data_path.glob('*'))
        print(f"  Data folder size: {len(files_in_data)} file(s)")
        if len(files_in_data) == 0:
            print("  ✓ Ready for database initialization")
        else:
            print("  Files present:")
            for f in files_in_data:
                print(f"    - {f.name}")
    
    # Summary
    print("\n" + "=" * 70)
    if all_folders_exist and all_files_exist:
        print("✓ STRUCTURE VERIFICATION PASSED")
        print("\nNext steps:")
        print("  1. pip install -r requirements.txt")
        print("  2. python scripts/init_local_db.py")
        print("  3. python -m backend.api_server")
        print("\nSee README.md for detailed setup instructions.")
        return 0
    else:
        print("✗ STRUCTURE VERIFICATION FAILED")
        print("\nMissing files detected. Please check above.")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(verify_structure())
