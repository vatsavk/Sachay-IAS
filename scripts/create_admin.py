import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sanchay_db
from auth import hash_password

def create_admin(name, email, password):
    sanchay_db.init_database()
    
    hashed = hash_password(password)
    
    # Check if admin already exists
    existing = sanchay_db.get_user_by_email(email)
    if existing:
        print(f"Admin user {email} already exists! Updating password and role...")
        with sanchay_db.get_connection() as conn:
            conn.execute('UPDATE users SET password_hash = ?, role = ? WHERE email = ?', 
                         (hashed, 'admin', email))
        return existing['user_id']
        
    user_id = sanchay_db.insert_user_with_password(
        name=name,
        email=email,
        password_hash=hashed,
        role='admin',
        status='active'
    )
    print(f"Successfully created admin user: {email} with ID: {user_id}")
    return user_id

if __name__ == '__main__':
    print("Seeding Principal Consultant...")
    create_admin('System Admin', 'admin@sanchay.io', 'secureadmin2026')
