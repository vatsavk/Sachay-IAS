"""
SANCHAY Database Operations Tests
Comprehensive testing of database layer and SQL operations
"""
import pytest
import sqlite3
import sanchay_db
from datetime import datetime

pytestmark = pytest.mark.database

class TestDatabaseConnection:
    """Test database connection and initialization"""
    
    def test_database_initialization(self, test_db_path):
        """Test that database is properly initialized with all tables"""
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Check for all required tables
        required_tables = ['users', 'advisors', 'clients', 'goals', 'tasks', 'transactions']
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            assert table in existing_tables, f"Missing table: {table}"
        
        conn.close()
    
    def test_database_path_assignment(self, test_db_path):
        """Test that database path can be assigned"""
        assert test_db_path is not None
        assert test_db_path.endswith('.db')
    
    def test_connection_context_manager(self, test_db_path):
        """Test using connection as context manager"""
        with sanchay_db.get_connection(test_db_path) as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result is not None
    
    def test_foreign_key_enforcement(self, test_db_path):
        """Test that foreign key constraints are enforced"""
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            
            # Try to insert a client with non-existent user_id
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    'INSERT INTO clients (user_id, advisor_id) VALUES (?, ?)',
                    (99999, None)
                )
                conn.commit()

class TestUserOperations:
    """Test user CRUD operations"""
    
    def test_insert_user(self, test_db_path, clean_db):
        """Test inserting a user"""
        user_id = sanchay_db.insert_user(
            name='John Doe',
            email='john@test.io',
            phone='+91-9999999999',
            role='advisor',
            status='active'
        )
        
        assert user_id > 0
        
        # Verify user was inserted
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row['email'] == 'john@test.io'
    
    def test_get_user_by_email(self, test_db_path, clean_db):
        """Test retrieving user by email"""
        # Insert user
        sanchay_db.insert_user(
            name='Jane Doe',
            email='jane@test.io',
            role='client'
        )
        
        # Retrieve user
        user = sanchay_db.get_user_by_email('jane@test.io')
        assert user is not None
        assert user['name'] == 'Jane Doe'
        assert user['role'] == 'client'
    
    def test_get_nonexistent_user(self, test_db_path, clean_db):
        """Test retrieving non-existent user returns None"""
        user = sanchay_db.get_user_by_email('nonexistent@test.io')
        assert user is None
    
    def test_ensure_user_creates_new(self, test_db_path, clean_db):
        """Test ensure_user creates new user if not exists"""
        user_id = sanchay_db.ensure_user(
            name='New User',
            email='newuser@test.io',
            role='advisor'
        )
        
        assert user_id > 0
        
        # Verify user was created
        user = sanchay_db.get_user_by_email('newuser@test.io')
        assert user is not None
    
    def test_ensure_user_returns_existing(self, test_db_path, clean_db):
        """Test ensure_user returns existing user without duplicate"""
        # Create user
        user_id1 = sanchay_db.ensure_user(
            name='Existing User',
            email='existing@test.io',
            role='client'
        )
        
        # Ensure same user again
        user_id2 = sanchay_db.ensure_user(
            name='Different Name',  # Different name, should not create new record
            email='existing@test.io',
            role='advisor'
        )
        
        # Should return same ID
        assert user_id1 == user_id2
    
    def test_duplicate_email_constraint(self, test_db_path, clean_db):
        """Test that duplicate emails are rejected"""
        sanchay_db.insert_user(
            name='User 1',
            email='duplicate@test.io',
            role='advisor'
        )
        
        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            sanchay_db.insert_user(
                name='User 2',
                email='duplicate@test.io',
                role='client'
            )
    
    def test_user_role_constraint(self, test_db_path, clean_db):
        """Test user role CHECK constraint"""
        valid_roles = ['advisor', 'client', 'principal_consultant']
        
        for role in valid_roles:
            user_id = sanchay_db.insert_user(
                name=f'User_{role}',
                email=f'{role}@test.io',
                role=role
            )
            assert user_id > 0

class TestAdvisorOperations:
    """Test advisor-specific operations"""
    
    def test_create_advisor(self, test_db_path, clean_db):
        """Test creating an advisor"""
        advisor_id = sanchay_db.create_advisor(
            name='Advisor Name',
            email='advisor@test.io',
            firm_name='Test Firm',
            license_no='LIC123'
        )
        
        assert advisor_id > 0
        
        # Verify advisor was created with linked user
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT a.*, u.name FROM advisors a JOIN users u ON a.user_id = u.user_id WHERE a.advisor_id = ?', (advisor_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row['firm_name'] == 'Test Firm'
    
    def test_ensure_advisor_creates_new(self, test_db_path, clean_db):
        """Test ensure_advisor creates new if not exists"""
        advisor_id = sanchay_db.ensure_advisor(
            name='New Advisor',
            email='newadvisor@test.io',
            firm_name='New Firm',
            license_no='NEW123'
        )
        
        assert advisor_id > 0
    
    def test_ensure_advisor_returns_existing(self, test_db_path, clean_db):
        """Test ensure_advisor returns existing advisor"""
        advisor_id1 = sanchay_db.ensure_advisor(
            name='Same Advisor',
            email='same@test.io',
            firm_name='Same Firm',
            license_no='SAME123'
        )
        
        advisor_id2 = sanchay_db.ensure_advisor(
            name='Different Name',
            email='same@test.io',
            firm_name='Different Firm',
            license_no='DIFF123'
        )
        
        assert advisor_id1 == advisor_id2

class TestClientOperations:
    """Test client-related operations"""
    
    def test_create_client(self, test_db_path, clean_db):
        """Test creating a client"""
        # Create user first
        user_id = sanchay_db.insert_user('Client Name', 'client@test.io', role='client')
        
        # Create client
        client_id = sanchay_db.create_client(
            user_id=user_id,
            advisor_id=None,
            dob='1990-01-01',
            income=50.0,
            net_worth=100.0,
            occupation='Business',
            onboarding_date='2023-01-01'
        )
        
        assert client_id > 0
        
        # Verify client was created
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clients WHERE client_id = ?', (client_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row['income'] == 50.0
    
    def test_list_clients(self, test_db_path, clean_db):
        """Test listing all clients"""
        # Create multiple clients
        for i in range(3):
            user_id = sanchay_db.insert_user(f'Client{i}', f'client{i}@test.io', role='client')
            sanchay_db.create_client(user_id, None)
        
        clients = sanchay_db.list_clients()
        
        assert isinstance(clients, list)
        assert len(clients) >= 3
    
    def test_client_with_advisor(self, test_db_path, clean_db):
        """Test creating client with advisor relationship"""
        # Create advisor
        advisor_id = sanchay_db.create_advisor('Advisor', 'advisor@test.io', 'Firm', 'LIC123')
        
        # Create client
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id, advisor_id)
        
        # Verify relationship
        clients = sanchay_db.list_clients()
        client = next((c for c in clients if c['client_id'] == client_id), None)
        
        assert client is not None
        assert client['advisor_id'] == advisor_id

class TestGoalOperations:
    """Test goal-related operations"""
    
    def test_create_goal(self, test_db_path, clean_db):
        """Test creating a goal"""
        # Create client
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        
        # Create goal
        goal_id = sanchay_db.create_goal(
            client_id=client_id,
            goal_type='Retirement',
            target_amount=5000000.0,
            target_date='2035',
            priority='High',
            status='On Track'
        )
        
        assert goal_id > 0
    
    def test_list_goals(self, test_db_path, clean_db):
        """Test listing goals"""
        # Create client and goal
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        sanchay_db.create_goal(client_id, 'Retirement', 5000000.0, '2035')
        
        goals = sanchay_db.list_goals()
        
        assert isinstance(goals, list)
        assert len(goals) > 0
    
    def test_goal_invalid_client(self, test_db_path, clean_db):
        """Test that goal creation fails with invalid client"""
        with pytest.raises(sqlite3.IntegrityError):
            sanchay_db.create_goal(
                client_id=99999,
                goal_type='Test',
                target_amount=1000000.0,
                target_date='2035'
            )
    
    def test_multiple_goals_per_client(self, test_db_path, clean_db):
        """Test creating multiple goals for same client"""
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        
        goals_data = [
            ('Retirement', 5000000.0, '2035'),
            ('Education', 2000000.0, '2030'),
            ('Home', 3000000.0, '2028')
        ]
        
        goal_ids = []
        for goal_type, target, date in goals_data:
            goal_id = sanchay_db.create_goal(client_id, goal_type, target, date)
            goal_ids.append(goal_id)
        
        assert len(set(goal_ids)) == 3  # All different IDs

class TestTaskOperations:
    """Test task-related operations"""
    
    def test_create_task(self, test_db_path, clean_db):
        """Test creating a task"""
        # Create advisor
        advisor_id = sanchay_db.create_advisor('Advisor', 'advisor@test.io', 'Firm', 'LIC123')
        
        # Create client
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        
        # Create task
        task_id = sanchay_db.create_task(
            advisor_id=advisor_id,
            client_id=client_id,
            task_type='Portfolio Review',
            priority='High',
            due_date='2023-11-01',
            status='Pending'
        )
        
        assert task_id > 0
    
    def test_list_tasks(self, test_db_path, clean_db):
        """Test listing tasks"""
        # Setup
        advisor_id = sanchay_db.create_advisor('Advisor', 'advisor@test.io', 'Firm', 'LIC123')
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        
        sanchay_db.create_task(advisor_id, client_id, 'Task1', 'High', None, 'Pending')
        
        tasks = sanchay_db.list_tasks()
        assert isinstance(tasks, list)
    
    def test_set_task_status(self, test_db_path, clean_db):
        """Test updating task status"""
        # Setup
        advisor_id = sanchay_db.create_advisor('Advisor', 'advisor@test.io', 'Firm', 'LIC123')
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        
        task_id = sanchay_db.create_task(advisor_id, client_id, 'Task', 'High')
        
        # Update status
        rows_affected = sanchay_db.set_task_status(task_id, 'Completed')
        assert rows_affected > 0
        
        # Verify status changed
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            assert row['status'] == 'Completed'

class TestTransactionOperations:
    """Test transaction-related operations"""
    
    def test_create_transaction(self, test_db_path, clean_db):
        """Test creating a transaction"""
        # Create client
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        
        # Create transaction
        txn_id = sanchay_db.create_transaction(
            client_id=client_id,
            asset_id=1,
            txn_type='Purchase',
            quantity=100.0,
            price=1500.0,
            txn_date='2023-10-17'
        )
        
        assert txn_id > 0
    
    def test_list_transactions(self, test_db_path, clean_db):
        """Test listing transactions"""
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        sanchay_db.create_transaction(client_id, 1, 'Purchase', 100.0, 1500.0)
        
        transactions = sanchay_db.list_transactions()
        assert isinstance(transactions, list)
    
    def test_transaction_with_all_fields(self, test_db_path, clean_db):
        """Test transaction with all fields populated"""
        user_id = sanchay_db.insert_user('Client', 'client@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        
        txn_id = sanchay_db.create_transaction(
            client_id=client_id,
            asset_id=100,
            txn_type='Sale',
            quantity=50.5,
            price=2000.75,
            txn_date='2023-10-15'
        )
        
        # Verify transaction
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions WHERE txn_id = ?', (txn_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row['quantity'] == 50.5
            assert row['price'] == 2000.75

class TestDataConsistency:
    """Test data consistency and referential integrity"""
    
    def test_cascade_delete_on_user(self, test_db_path, clean_db):
        """Test cascade delete when user is deleted"""
        # Create user
        user_id = sanchay_db.insert_user('User', 'user@test.io', role='client')
        client_id = sanchay_db.create_client(user_id)
        goal_id = sanchay_db.create_goal(client_id, 'Goal', 1000000.0, '2035')
        
        # Delete user (should cascade delete client and goal)
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()
        
        # Verify client and goal are deleted
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as cnt FROM clients WHERE client_id = ?', (client_id,))
            assert cursor.fetchone()['cnt'] == 0
            
            cursor.execute('SELECT COUNT(*) as cnt FROM goals WHERE goal_id = ?', (goal_id,))
            assert cursor.fetchone()['cnt'] == 0
    
    def test_timestamp_creation(self, test_db_path, clean_db):
        """Test that created_at timestamps are set"""
        user_id = sanchay_db.insert_user('User', 'user@test.io', role='client')
        
        # Verify timestamp was set
        with sanchay_db.get_connection(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT created_at FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            assert row['created_at'] is not None
