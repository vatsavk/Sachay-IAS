import sqlite3
import os

DB_PATH = 'sanchay_local.db'


def build_database(path=DB_PATH):
    if os.path.exists(path):
        print(f"Overwriting existing database: {path}")
        try:
            os.remove(path)
        except PermissionError:
            print(f"Warning: Could not delete existing DB file, it may be in use: {path}")
            return

    conn = sqlite3.connect(path)
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()

    # 3.1 USERS & CLIENT SYSTEM
    cur.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        role TEXT CHECK(role IN ('advisor','client','principal_consultant','compliance_officer')),
        status TEXT,
        password_hash TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cur.execute('''
    CREATE TABLE advisors (
        advisor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        firm_name TEXT,
        license_no TEXT,
        experience_years INTEGER
    );
    ''')

    cur.execute('''
    CREATE TABLE clients (
        client_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        advisor_id INTEGER REFERENCES advisors(advisor_id) ON DELETE SET NULL,
        dob DATE,
        income NUMERIC,
        net_worth NUMERIC,
        occupation TEXT,
        onboarding_date DATE,
        advisory_fee_bps INTEGER DEFAULT 100
    );
    ''')

    # 3.2 CLIENT PROFILE
    cur.execute('''
    CREATE TABLE risk_profiles (
        risk_profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        risk_score INTEGER,
        risk_category TEXT,
        liquidity_score INTEGER,
        investment_horizon INTEGER,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cur.execute('''
    CREATE TABLE financial_profiles (
        profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        monthly_income NUMERIC,
        monthly_expenses NUMERIC,
        assets_value NUMERIC,
        liabilities_value NUMERIC,
        surplus NUMERIC
    );
    ''')

    cur.execute('''
    CREATE TABLE goals (
        goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        goal_type TEXT,
        target_amount NUMERIC,
        target_date DATE,
        priority INTEGER,
        status TEXT
    );
    ''')

    # 3.3 ASSET SYSTEM
    cur.execute('''
    CREATE TABLE asset_categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE
    );
    ''')

    cur.execute('''
    CREATE TABLE asset_master (
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

    # 3.4 PORTFOLIO
    cur.execute('''
    CREATE TABLE portfolios (
        portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        total_value NUMERIC,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cur.execute('''
    CREATE TABLE holdings (
        holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
        portfolio_id INTEGER NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
        asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id) ON DELETE CASCADE,
        quantity NUMERIC,
        avg_buy_price NUMERIC,
        allocation_percent NUMERIC
    );
    ''')

    # 3.5 TRANSACTIONS
    cur.execute('''
    CREATE TABLE transactions (
        txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id) ON DELETE CASCADE,
        txn_type TEXT CHECK(txn_type IN ('BUY','SELL','SIP','SWITCH','DIVIDEND')),
        quantity NUMERIC,
        price NUMERIC,
        txn_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # 3.6 FX ENGINE
    cur.execute('''
    CREATE TABLE fx_rates_daily (
        fx_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        from_currency TEXT NOT NULL,
        to_currency TEXT NOT NULL DEFAULT 'INR',
        rate NUMERIC NOT NULL,
        version INTEGER NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        source TEXT DEFAULT 'RBI',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    );
    ''')

    cur.execute('''
    CREATE UNIQUE INDEX ux_fx_active
    ON fx_rates_daily(date, from_currency, to_currency)
    WHERE is_active = 1;
    ''')

    # 3.7 MONTHLY FX
    cur.execute('''
    CREATE TABLE fx_rates_monthly (
        fx_month_id INTEGER PRIMARY KEY AUTOINCREMENT,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        from_currency TEXT NOT NULL,
        to_currency TEXT NOT NULL,
        avg_rate NUMERIC
    );
    ''')

    # 3.8 TRANSACTION FX LOCK
    cur.execute('''
    CREATE TABLE fx_transaction_rates (
        txn_fx_id INTEGER PRIMARY KEY AUTOINCREMENT,
        txn_id INTEGER NOT NULL REFERENCES transactions(txn_id) ON DELETE CASCADE,
        fx_rate_used NUMERIC,
        rate_date DATE
    );
    ''')

    # 3.9 PRICE STORAGE
    cur.execute('''
    CREATE TABLE asset_prices (
        price_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id) ON DELETE CASCADE,
        price NUMERIC,
        price_date DATETIME,
        source TEXT
    );
    ''')

    # 3.10 VALUATION ENGINE
    cur.execute('''
    CREATE TABLE holding_valuations (
        valuation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        holding_id INTEGER NOT NULL REFERENCES holdings(holding_id) ON DELETE CASCADE,
        valuation_date DATETIME,
        price NUMERIC,
        fx_rate NUMERIC,
        fx_rate_type TEXT CHECK(fx_rate_type IN ('monthly','txn')),
        total_value_in_inr NUMERIC
    );
    ''')

    # 3.11 PORTFOLIO AGGREGATION
    cur.execute('''
    CREATE TABLE portfolio_aggregates (
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

    # 3.12 RECOMMENDATION ENGINE
    cur.execute('''
    CREATE TABLE recommendations (
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

    cur.execute('''
    CREATE TABLE recommendation_details (
        detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recommendation_id INTEGER NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
        asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id) ON DELETE CASCADE,
        suggested_allocation NUMERIC,
        action TEXT
    );
    ''')

    cur.execute('''
    CREATE TABLE advisor_overrides (
        override_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recommendation_id INTEGER NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
        advisor_id INTEGER NOT NULL REFERENCES advisors(advisor_id) ON DELETE CASCADE,
        override_reason TEXT,
        final_decision TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # 3.13 ML / PREDICTIONS
    cur.execute('''
    CREATE TABLE predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        attrition_risk_score NUMERIC,
        portfolio_growth_forecast NUMERIC,
        risk_shift_probability NUMERIC,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cur.execute('''
    CREATE TABLE model_versions (
        model_id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT,
        version TEXT,
        accuracy NUMERIC,
        deployed_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # 3.14 TASK & WORKFLOW
    cur.execute('''
    CREATE TABLE tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        advisor_id INTEGER NOT NULL REFERENCES advisors(advisor_id) ON DELETE SET NULL,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        task_type TEXT,
        priority TEXT,
        due_date DATE,
        status TEXT,
        owner_id INTEGER,
        category TEXT DEFAULT 'General',
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cur.execute('''
    CREATE TABLE email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT,
        subject TEXT,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        error_message TEXT
    );
    ''')

    cur.execute('''
    CREATE TABLE workflows (
        workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_name TEXT,
        trigger_event TEXT,
        action_type TEXT
    );
    ''')

    # 3.15 REPORT CACHE
    cur.execute('''
    CREATE TABLE report_cache (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(client_id) ON DELETE CASCADE,
        report_type TEXT,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        report_data JSON
    );
    ''')

    # 3.16 AUDIT LOGS
    cur.execute('''
    CREATE TABLE audit_logs (
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

    # 3.16.1 OPPORTUNITIES
    cur.execute('''
    CREATE TABLE opportunities (
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

    # 3.16.2 FAMILY RELATIONSHIPS
    cur.execute('''
    CREATE TABLE family_relationships (
        relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        related_client_id INTEGER REFERENCES clients(client_id) ON DELETE SET NULL,
        relation_type TEXT NOT NULL,
        family_name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # 3.17 FX INGESTION LOGS
    cur.execute('''
    CREATE TABLE fx_ingestion_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date DATE,
        status TEXT,
        records_inserted INTEGER,
        error_message TEXT
    );
    ''')

    # 3.18 PORTFOLIO SNAPSHOTS & EVENTS
    cur.execute('''
    CREATE TABLE portfolio_historical_snapshots (
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

    cur.execute('''
    CREATE TABLE portfolio_events (
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

    # Create notifications table
    cur.execute('''
    CREATE TABLE notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
        advisor_id INTEGER REFERENCES advisors(advisor_id) ON DELETE SET NULL,
        type TEXT,
        content TEXT,
        consent_status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Create meeting_minutes table
    cur.execute('''
    CREATE TABLE meeting_minutes (
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

    # Indexes for performance
    cur.executescript('''
    CREATE INDEX idx_clients_advisor ON clients(advisor_id);
    CREATE INDEX idx_transactions_client ON transactions(client_id);
    CREATE INDEX idx_assets_category ON asset_master(category_id);
    CREATE INDEX idx_portfolios_client ON portfolios(client_id);
    CREATE INDEX idx_holdings_portfolio ON holdings(portfolio_id);
    CREATE INDEX idx_recommendations_client ON recommendations(client_id);
    CREATE INDEX idx_predictions_client ON predictions(client_id);
    CREATE INDEX idx_tasks_advisor ON tasks(advisor_id);
    CREATE INDEX idx_tasks_client ON tasks(client_id);
    CREATE UNIQUE INDEX idx_client_snapshot_date ON portfolio_historical_snapshots(client_id, snapshot_date);
    CREATE INDEX idx_events_client ON portfolio_events(client_id);
    CREATE INDEX idx_opportunities_client ON opportunities(client_id);
    ''')

    conn.commit()
    conn.close()
    print(f"Database created and initialized at {path}")

if __name__ == "__main__":
    build_database()
