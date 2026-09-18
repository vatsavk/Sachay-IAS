import sqlite3
import os
import re
from contextlib import contextmanager
from pathlib import Path

_ROOT = Path(__file__).parent
DB_PATH = str(os.environ.get('SANCHAY_DB_PATH', _ROOT / 'sanchay_local.db'))
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith('postgres'))

if IS_POSTGRES:
    import psycopg2
    from psycopg2.extras import DictCursor

def translate_query(query):
    if not IS_POSTGRES:
        return query
    
    # Replace ? with %s
    query = query.replace('?', '%s')
    
    # Translate INTEGER PRIMARY KEY AUTOINCREMENT to SERIAL PRIMARY KEY
    query = re.sub(r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b', 'SERIAL PRIMARY KEY', query, flags=re.IGNORECASE)
    
    # Translate DATETIME to TIMESTAMP
    query = re.sub(r'\bDATETIME\b', 'TIMESTAMP', query, flags=re.IGNORECASE)
    
    return query

class DBCursor:
    def __init__(self, cur):
        self.cur = cur

    def execute(self, query, vars=None):
        translated = translate_query(query)
        if vars is not None:
            self.cur.execute(translated, vars)
        else:
            self.cur.execute(translated)
        return self

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()

    @property
    def rowcount(self):
        return self.cur.rowcount

    @property
    def lastrowid(self):
        if not IS_POSTGRES and hasattr(self.cur, 'lastrowid'):
            return self.cur.lastrowid
        return None

class DBConnection:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return DBCursor(self.conn.cursor())

    def execute(self, query, vars=None):
        cur = self.cursor()
        cur.execute(query, vars)
        return cur

    def executescript(self, script):
        if IS_POSTGRES:
            cur = self.cursor()
            cur.execute(script)
        else:
            self.conn.executescript(script)
            
    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

@contextmanager
def get_connection(path=None):
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        wrapped_conn = DBConnection(conn)
        try:
            yield wrapped_conn
        finally:
            wrapped_conn.commit()
            wrapped_conn.close()
    else:
        if path is None:
            path = DB_PATH
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON;')
        wrapped_conn = DBConnection(conn)
        try:
            yield wrapped_conn
        finally:
            wrapped_conn.commit()
            wrapped_conn.close()


def init_database(path=DB_PATH):
    # Create the database and essential tables if missing.
    with get_connection(path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                role TEXT CHECK(role IN (
                                  'advisor','client',
                                  'principal_consultant','compliance_officer'
                              )),
                status TEXT,
                password_hash TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        if not IS_POSTGRES:
            # Migration: widen role constraint and add password_hash
            try:
                cur = conn.cursor()
                cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
                ddl = str(cur.fetchone() or '')
                if "'advisor','client','admin'" in ddl:
                    conn.executescript('''
                        ALTER TABLE users RENAME TO users_old;
                        CREATE TABLE users (
                            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                            name          TEXT NOT NULL,
                            email         TEXT NOT NULL UNIQUE,
                            phone         TEXT,
                            role          TEXT CHECK(role IN (
                                              'advisor','client',
                                              'principal_consultant','compliance_officer'
                                          )),
                            status        TEXT,
                            password_hash TEXT,
                            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                        );
                        INSERT INTO users (user_id, name, email, phone, role, status, created_at)
                        SELECT user_id, name, email, phone, role, status, created_at FROM users_old;
                        DROP TABLE users_old;
                    ''')
                elif "password_hash" not in ddl:
                    conn.execute('ALTER TABLE users ADD COLUMN password_hash TEXT;')
            except Exception:
                pass

        conn.execute('''
            CREATE TABLE IF NOT EXISTS advisors (
                advisor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                firm_name TEXT,
                license_no TEXT,
                experience_years INTEGER
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                advisor_id INTEGER REFERENCES advisors(advisor_id) ON DELETE SET NULL,
                dob DATE,
                income NUMERIC,
                net_worth NUMERIC,
                occupation TEXT,
                onboarding_date DATE
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                goal_type TEXT,
                target_amount NUMERIC,
                target_date DATE,
                priority TEXT,
                status TEXT
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                advisor_id INTEGER REFERENCES advisors(advisor_id) ON DELETE SET NULL,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                task_type TEXT,
                priority TEXT,
                due_date DATE,
                status TEXT
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                asset_id INTEGER,
                txn_type TEXT,
                quantity NUMERIC,
                price NUMERIC,
                txn_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                advisor_id INTEGER REFERENCES advisors(advisor_id) ON DELETE SET NULL,
                type TEXT,
                content TEXT,
                consent_status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS meeting_minutes (
                minutes_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id    INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                advisor_id   INTEGER REFERENCES advisors(advisor_id) ON DELETE SET NULL,
                meeting_date DATE NOT NULL,
                agenda       TEXT,
                discussion   TEXT NOT NULL,
                action_items TEXT,
                sent_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        def safe_alter(query):
            try:
                if IS_POSTGRES:
                    conn.execute("SAVEPOINT sp_alter")
                    conn.execute(query)
                    conn.execute("RELEASE SAVEPOINT sp_alter")
                else:
                    conn.execute(query)
            except Exception:
                if IS_POSTGRES:
                    conn.execute("ROLLBACK TO SAVEPOINT sp_alter")

        conn.execute('''
            CREATE TABLE IF NOT EXISTS asset_categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL UNIQUE
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS asset_master (
                asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_name TEXT NOT NULL,
                category_id INTEGER REFERENCES asset_categories(category_id) ON DELETE SET NULL,
                base_currency TEXT,
                risk_level TEXT,
                liquidity_type TEXT,
                sector TEXT DEFAULT 'General',
                market_cap_category TEXT DEFAULT 'Large Cap',
                investment_factor TEXT DEFAULT 'Growth'
            );
        ''')
        safe_alter('CREATE INDEX idx_assets_category ON asset_master(category_id);')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                total_value NUMERIC,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        safe_alter('CREATE INDEX idx_portfolios_client ON portfolios(client_id);')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
                asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id) ON DELETE CASCADE,
                quantity NUMERIC,
                avg_buy_price NUMERIC,
                allocation_percent NUMERIC
            );
        ''')
        safe_alter('CREATE INDEX idx_holdings_portfolio ON holdings(portfolio_id);')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS asset_prices (
                price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id) ON DELETE CASCADE,
                price NUMERIC,
                price_date DATETIME,
                source TEXT
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS risk_profiles (
                risk_profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                risk_score INTEGER,
                risk_category TEXT,
                liquidity_score INTEGER,
                investment_horizon INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS financial_profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                monthly_income NUMERIC,
                monthly_expenses NUMERIC,
                assets_value NUMERIC,
                liabilities_value NUMERIC,
                surplus NUMERIC
            );
        ''')

        # Migrations for asset_master metadata
        safe_alter("ALTER TABLE asset_master ADD COLUMN sector TEXT DEFAULT 'General';")
        safe_alter("ALTER TABLE asset_master ADD COLUMN market_cap_category TEXT DEFAULT 'Large Cap';")
        safe_alter("ALTER TABLE asset_master ADD COLUMN investment_factor TEXT DEFAULT 'Growth';")

        # portfolio_historical_snapshots table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_historical_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                snapshot_date DATE NOT NULL,
                total_value NUMERIC NOT NULL,
                equity_value NUMERIC NOT NULL,
                debt_value NUMERIC NOT NULL,
                gold_value NUMERIC NOT NULL,
                cash_value NUMERIC NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        safe_alter('CREATE UNIQUE INDEX idx_client_snapshot_date ON portfolio_historical_snapshots(client_id, snapshot_date);')

        # portfolio_events table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER REFERENCES clients(client_id) ON DELETE CASCADE,
                asset_id INTEGER REFERENCES asset_master(asset_id) ON DELETE SET NULL,
                event_type TEXT NOT NULL,
                security_name TEXT,
                event_date DATE NOT NULL,
                severity NUMERIC NOT NULL,
                sensitivity NUMERIC NOT NULL,
                recommended_action TEXT,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        safe_alter('CREATE INDEX idx_events_client ON portfolio_events(client_id);')

        # Migrations for Phase 1 Advisor OS
        safe_alter("ALTER TABLE clients ADD COLUMN advisory_fee_bps INTEGER DEFAULT 100;")

        safe_alter("ALTER TABLE tasks ADD COLUMN owner_id INTEGER;")
        safe_alter("ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'General';")
        safe_alter("ALTER TABLE tasks ADD COLUMN description TEXT;")
        safe_alter("ALTER TABLE tasks ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")

        safe_alter("ALTER TABLE audit_logs ADD COLUMN before_value TEXT;")
        safe_alter("ALTER TABLE audit_logs ADD COLUMN after_value TEXT;")

        # Create opportunities table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                expected_benefit TEXT,
                revenue_potential NUMERIC DEFAULT 0,
                client_impact TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        safe_alter('CREATE INDEX IF NOT EXISTS idx_opportunities_client ON opportunities(client_id);')

        # Create family_relationships table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS family_relationships (
                relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                related_client_id INTEGER REFERENCES clients(client_id) ON DELETE SET NULL,
                relation_type TEXT NOT NULL,
                family_name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS fx_rates_daily (
        fx_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        from_currency TEXT NOT NULL,
        to_currency TEXT NOT NULL DEFAULT 'INR',
        rate NUMERIC NOT NULL,
        version INTEGER NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        source TEXT DEFAULT 'RBI',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS fx_rates_monthly (
        fx_month_id INTEGER PRIMARY KEY AUTOINCREMENT,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        from_currency TEXT NOT NULL,
        to_currency TEXT NOT NULL,
        avg_rate NUMERIC
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS fx_transaction_rates (
        txn_fx_id INTEGER PRIMARY KEY AUTOINCREMENT,
        txn_id INTEGER NOT NULL REFERENCES transactions(txn_id) ON DELETE CASCADE,
        fx_rate_used NUMERIC,
        rate_date DATE
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS holding_valuations (
        valuation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        holding_id INTEGER NOT NULL REFERENCES holdings(holding_id) ON DELETE CASCADE,
        valuation_date DATETIME,
        price NUMERIC,
        fx_rate NUMERIC,
        fx_rate_type TEXT CHECK(fx_rate_type IN ('monthly','txn')),
        total_value_in_inr NUMERIC
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_aggregates (
        agg_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        total_value NUMERIC,
        equity_value NUMERIC,
        debt_value NUMERIC,
        mf_value NUMERIC,
        insurance_value NUMERIC,
        alternative_value NUMERIC,
        last_computed DATETIME DEFAULT CURRENT_TIMESTAMP
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
        recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        scenario_type TEXT CHECK(scenario_type IN ('primary','alternative')),
        expected_return NUMERIC,
        risk_score NUMERIC,
        liquidity_impact NUMERIC,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS recommendation_details (
        detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recommendation_id INTEGER NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
        asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id) ON DELETE CASCADE,
        suggested_allocation NUMERIC,
        action TEXT
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS advisor_overrides (
        override_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recommendation_id INTEGER NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
        advisor_id INTEGER NOT NULL REFERENCES advisors(advisor_id) ON DELETE CASCADE,
        override_reason TEXT,
        final_decision TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        attrition_risk_score NUMERIC,
        portfolio_growth_forecast NUMERIC,
        risk_shift_probability NUMERIC,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS model_versions (
        model_id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT,
        version TEXT,
        accuracy NUMERIC,
        deployed_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
        workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_name TEXT,
        trigger_event TEXT,
        action_type TEXT
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS report_cache (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(client_id) ON DELETE CASCADE,
        report_type TEXT,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        report_data JSON
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT,
        entity_id INTEGER,
        action TEXT,
        performed_by INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        before_value TEXT,
        after_value TEXT
    );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS fx_ingestion_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date DATE,
        status TEXT,
        records_inserted INTEGER,
        error_message TEXT
    );
        ''')

    # Ensure at least one advisor exists
    ensure_advisor("System Advisor", "admin@sanchay.io", "Sanchayer Pros", "REG12345")

    return path


def create_advisor(name, email, firm_name, license_no):
    user_id = ensure_user(name, email, role='advisor')
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO advisors (user_id, firm_name, license_no) VALUES (?, ?, ?) RETURNING advisor_id',
                (user_id, firm_name, license_no)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO advisors (user_id, firm_name, license_no) VALUES (?, ?, ?)',
                (user_id, firm_name, license_no)
            )
            return cur.lastrowid


def ensure_advisor(name, email, firm_name, license_no):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT a.advisor_id FROM advisors a JOIN users u ON a.user_id = u.user_id WHERE u.email = ?', (email,))
        row = cur.fetchone()
        if row:
            return row['advisor_id']
    return create_advisor(name, email, firm_name, license_no)


def insert_user(name, email, phone=None, role='advisor', status='active'):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO users (name, email, phone, role, status) VALUES (?, ?, ?, ?, ?) RETURNING user_id',
                (name, email, phone, role, status)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO users (name, email, phone, role, status) VALUES (?, ?, ?, ?, ?)',
                (name, email, phone, role, status)
            )
            return cur.lastrowid

def insert_user_with_password(name, email, password_hash, phone=None, role='advisor', status='active'):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO users (name, email, phone, role, status, password_hash) VALUES (?, ?, ?, ?, ?, ?) RETURNING user_id',
                (name, email, phone, role, status, password_hash)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO users (name, email, phone, role, status, password_hash) VALUES (?, ?, ?, ?, ?, ?)',
                (name, email, phone, role, status, password_hash)
            )
            return cur.lastrowid


def get_user_by_email(email):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_clients():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT c.*, u.name AS name, u.email AS email, u.name AS client_name, u.email AS client_email, a.firm_name AS advisor FROM clients c LEFT JOIN users u ON c.user_id = u.user_id LEFT JOIN advisors a ON c.advisor_id = a.advisor_id')
        return [dict(r) for r in cur.fetchall()]

def list_clients_by_advisor(advisor_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT c.*, u.name AS name, u.email AS email, u.name AS client_name, u.email AS client_email, a.firm_name AS advisor FROM clients c LEFT JOIN users u ON c.user_id = u.user_id LEFT JOIN advisors a ON c.advisor_id = a.advisor_id WHERE c.advisor_id = ?', (advisor_id,))
        return [dict(r) for r in cur.fetchall()]


def create_client(user_id, advisor_id=None, dob=None, income=0, net_worth=0, occupation=None, onboarding_date=None):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO clients (user_id, advisor_id, dob, income, net_worth, occupation, onboarding_date) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING client_id',
                (user_id, advisor_id, dob, income, net_worth, occupation, onboarding_date)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO clients (user_id, advisor_id, dob, income, net_worth, occupation, onboarding_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, advisor_id, dob, income, net_worth, occupation, onboarding_date)
            )
            return cur.lastrowid


def ensure_user(name, email, phone=None, role='client', status='active'):
    existing = get_user_by_email(email)
    if existing:
        return existing['user_id']
    return insert_user(name, email, phone, role, status)


def list_goals():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM goals')
        return [dict(r) for r in cur.fetchall()]

def list_goals_by_advisor(advisor_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT g.* FROM goals g
            JOIN clients c ON g.client_id = c.client_id
            WHERE c.advisor_id = ?
        ''', (advisor_id,))
        return [dict(r) for r in cur.fetchall()]


def create_goal(client_id, goal_type, target_amount, target_date, priority='Medium', status='On Track'):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO goals (client_id, goal_type, target_amount, target_date, priority, status) VALUES (?, ?, ?, ?, ?, ?) RETURNING goal_id',
                (client_id, goal_type, target_amount, target_date, priority, status)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO goals (client_id, goal_type, target_amount, target_date, priority, status) VALUES (?, ?, ?, ?, ?, ?)',
                (client_id, goal_type, target_amount, target_date, priority, status)
            )
            return cur.lastrowid


def list_tasks():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM tasks')
        return [dict(r) for r in cur.fetchall()]

def list_tasks_by_advisor(advisor_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM tasks WHERE advisor_id = ?', (advisor_id,))
        return [dict(r) for r in cur.fetchall()]


def create_task(advisor_id, client_id, task_type, priority='Medium', due_date=None, status='Pending', owner_id=None, category='General', description=None):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO tasks (advisor_id, client_id, task_type, priority, due_date, status, owner_id, category, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING task_id',
                (advisor_id, client_id, task_type, priority, due_date, status, owner_id, category, description)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO tasks (advisor_id, client_id, task_type, priority, due_date, status, owner_id, category, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (advisor_id, client_id, task_type, priority, due_date, status, owner_id, category, description)
            )
            return cur.lastrowid

def create_notification(client_id, advisor_id, notif_type, content):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                "INSERT INTO notifications (client_id, advisor_id, type, content, consent_status) VALUES (?, ?, ?, ?, 'pending') RETURNING notification_id",
                (client_id, advisor_id, notif_type, content)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                "INSERT INTO notifications (client_id, advisor_id, type, content, consent_status) VALUES (?, ?, ?, ?, 'pending')",
                (client_id, advisor_id, notif_type, content)
            )
            return cur.lastrowid

def list_notifications(client_id=None, advisor_id=None):
    with get_connection() as conn:
        cur = conn.cursor()
        if client_id:
            cur.execute('SELECT * FROM notifications WHERE client_id = ? ORDER BY created_at DESC', (client_id,))
        elif advisor_id:
            cur.execute('SELECT * FROM notifications WHERE advisor_id = ? ORDER BY created_at DESC', (advisor_id,))
        else:
            cur.execute('SELECT * FROM notifications ORDER BY created_at DESC')
        return [dict(r) for r in cur.fetchall()]

def update_consent(notification_id, status):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'UPDATE notifications SET consent_status = ? WHERE notification_id = ?',
            (status, notification_id)
        )
        return cur.rowcount > 0


def set_task_status(task_id, status):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('UPDATE tasks SET status = ? WHERE task_id = ?', (status, task_id))
        return cur.rowcount


def list_transactions():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM transactions')
        return [dict(r) for r in cur.fetchall()]


def create_transaction(client_id, asset_id, txn_type, quantity, price, txn_date=None):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO transactions (client_id, asset_id, txn_type, quantity, price, txn_date) VALUES (?, ?, ?, ?, ?, ?) RETURNING txn_id',
                (client_id, asset_id, txn_type, quantity, price, txn_date)
            )
            return cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO transactions (client_id, asset_id, txn_type, quantity, price, txn_date) VALUES (?, ?, ?, ?, ?, ?)',
                (client_id, asset_id, txn_type, quantity, price, txn_date)
            )
            return cur.lastrowid


def list_events():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM report_cache WHERE report_type = ?', ('EVENTS',))
        return [dict(r) for r in cur.fetchall()]


def list_compliance():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM audit_logs WHERE entity_type = ?', ('COMPLIANCE',))
        return [dict(r) for r in cur.fetchall()]


def create_meeting_minutes(client_id, advisor_id, meeting_date, agenda, discussion, action_items):
    with get_connection() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute(
                'INSERT INTO meeting_minutes (client_id, advisor_id, meeting_date, agenda, discussion, action_items) VALUES (?, ?, ?, ?, ?, ?) RETURNING minutes_id',
                (client_id, advisor_id, meeting_date, agenda, discussion, action_items)
            )
            minutes_id = cur.fetchone()[0]
        else:
            cur.execute(
                'INSERT INTO meeting_minutes (client_id, advisor_id, meeting_date, agenda, discussion, action_items) VALUES (?, ?, ?, ?, ?, ?)',
                (client_id, advisor_id, meeting_date, agenda, discussion, action_items)
            )
            minutes_id = cur.lastrowid

        # Auto-create notification for the client
        cur.execute(
            "INSERT INTO notifications (client_id, advisor_id, type, content, consent_status) VALUES (?, ?, 'meeting_minutes', ?, 'pending')",
            (client_id, advisor_id, f'Meeting Minutes ({meeting_date}): {(discussion or "")[:400]}')
        )
        return minutes_id

def list_meeting_minutes(client_id=None, advisor_id=None):
    with get_connection() as conn:
        cur = conn.cursor()
        if client_id:
            cur.execute('SELECT * FROM meeting_minutes WHERE client_id = ? ORDER BY meeting_date DESC', (client_id,))
        elif advisor_id:
            cur.execute('SELECT * FROM meeting_minutes WHERE advisor_id = ? ORDER BY meeting_date DESC', (advisor_id,))
        else:
            cur.execute('SELECT * FROM meeting_minutes ORDER BY meeting_date DESC')
        return [dict(r) for r in cur.fetchall()]

def get_compliance_summary():
    with get_connection() as conn:
        cur = conn.cursor()
        total_clients = cur.execute('SELECT COUNT(*) FROM clients').fetchone()[0]
        pending_consents = cur.execute("SELECT COUNT(*) FROM notifications WHERE consent_status='pending'").fetchone()[0]
        agreed = cur.execute("SELECT COUNT(*) FROM notifications WHERE consent_status='agree'").fetchone()[0]
        disagreed = cur.execute("SELECT COUNT(*) FROM notifications WHERE consent_status='disagree'").fetchone()[0]
        minutes_count = cur.execute('SELECT COUNT(*) FROM meeting_minutes').fetchone()[0]
        return {
            'total_clients': total_clients,
            'pending_consents': pending_consents,
            'agreed': agreed,
            'disagreed': disagreed,
            'minutes_sent': minutes_count
        }

def get_client_holdings_valuation(client_id):
    """Calculates allocation values across categories (Equity, Debt, Gold, Cash) for a client."""
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT ac.category_name, SUM(h.quantity * COALESCE(ap.price, h.avg_buy_price)) as value
            FROM holdings h
            JOIN asset_master am ON h.asset_id = am.asset_id
            JOIN asset_categories ac ON am.category_id = ac.category_id
            LEFT JOIN asset_prices ap ON am.asset_id = ap.asset_id
                AND ap.price_id = (SELECT price_id FROM asset_prices WHERE asset_id = am.asset_id ORDER BY price_date DESC LIMIT 1)
            JOIN portfolios p ON h.portfolio_id = p.portfolio_id
            WHERE p.client_id = ?
            GROUP BY ac.category_name
        ''', (client_id,)).fetchall()
        return [dict(r) for r in rows]

def create_advisor_with_password(name, email, password_hash, firm_name='', license_no='', phone=None):
    with get_connection() as conn:
        cur = conn.cursor()
        # Upsert user
        cur.execute(
            'INSERT INTO users (name, email, phone, role, status, password_hash) VALUES (?, ?, ?, ?, ?, ?)'
            ' ON CONFLICT(email) DO UPDATE SET password_hash=excluded.password_hash, name=excluded.name',
            (name, email, phone, 'advisor', 'active', password_hash)
        )
        user_id = cur.execute('SELECT user_id FROM users WHERE email=?', (email,)).fetchone()['user_id']
        existing = cur.execute('SELECT advisor_id FROM advisors WHERE user_id=?', (user_id,)).fetchone()
        if not existing:
            if IS_POSTGRES:
                cur.execute('INSERT INTO advisors (user_id, firm_name, license_no) VALUES (?, ?, ?) RETURNING advisor_id', (user_id, firm_name, license_no))
                advisor_id = cur.fetchone()[0]
            else:
                cur.execute('INSERT INTO advisors (user_id, firm_name, license_no) VALUES (?, ?, ?)', (user_id, firm_name, license_no))
                advisor_id = cur.lastrowid
        else:
            advisor_id = existing['advisor_id']
        return {'user_id': user_id, 'advisor_id': advisor_id}

def get_portfolio_historical_snapshots(client_id):
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT snapshot_date, total_value, equity_value, debt_value, gold_value, cash_value
            FROM portfolio_historical_snapshots
            WHERE client_id = ?
            ORDER BY snapshot_date ASC
        ''', (client_id,)).fetchall()
        return [dict(r) for r in rows]

def get_portfolio_events(client_id):
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT event_id, event_type, security_name, event_date, severity, sensitivity, recommended_action, content, asset_id
            FROM portfolio_events
            WHERE client_id = ?
            ORDER BY event_date DESC
        ''', (client_id,)).fetchall()
        return [dict(r) for r in rows]

if __name__ == '__main__':
    print('Connecting to', 'PostgreSQL' if IS_POSTGRES else DB_PATH)
    with get_connection() as conn:
        if IS_POSTGRES:
            print('Version:', conn.execute('SELECT version()').fetchone()[0])
        else:
            print('Version:', conn.execute('SELECT sqlite_version()').fetchone()[0])

    # demo usage
    u = get_user_by_email('sanchay@example.com')
    if u is None:
        user_id = insert_user('SANCHAY Admin', 'sanchay@example.com', '+911234567890', 'admin', 'active')
        print('Inserted user_id:', user_id)
    else:
        print('Existing user:', u)

    users = list_clients()
    print('Clients count:', len(users))
