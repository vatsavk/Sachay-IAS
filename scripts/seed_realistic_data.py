# -*- coding: utf-8 -*-
"""
SANCHAY IAS -- Realistic Seed Data Script
Clears stale test data and seeds 15 real-world HNI Indian client profiles
with full portfolios, goals, tasks, transactions, and notifications.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
from pathlib import Path
from datetime import date, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sanchay_db
from auth import hash_password

conn_gen = sanchay_db.get_connection()
conn = conn_gen.__enter__()
IS_PG = sanchay_db.IS_POSTGRES

if not IS_PG:
    conn.execute('PRAGMA foreign_keys=OFF')

# ── WIPE CLIENT-SIDE DATA ────────────────────────────────────────────────────
print("Clearing stale data...")

def safe_run(query):
    try:
        if IS_PG:
            conn.execute("SAVEPOINT sp_run")
            conn.execute(query)
            conn.execute("RELEASE SAVEPOINT sp_run")
        else:
            conn.execute(query)
    except Exception as e:
        if IS_PG:
            conn.execute("ROLLBACK TO SAVEPOINT sp_run")
        return e
    return None

for tbl in ['notifications','meeting_minutes','transactions','portfolios',
            'portfolio_aggregates','holding_valuations','holdings',
            'goals','tasks','financial_profiles','risk_profiles',
            'predictions','recommendations','recommendation_details',
            'advisor_overrides','workflows','report_cache',
            'asset_prices','asset_master','asset_categories','fx_rates_daily']:
    err = safe_run(f'DELETE FROM {tbl}')
    if err:
        print(f'  Skip {tbl}: {err}')
    else:
        print(f'  Cleared {tbl}')

safe_run("DELETE FROM clients")
safe_run("DELETE FROM users WHERE email NOT IN ('admin@sanchay.io')")
safe_run("DELETE FROM advisors WHERE advisor_id > 1")

# Reset sequences
for tbl in ['clients','users','goals','tasks','portfolios','transactions',
            'notifications','meeting_minutes','asset_categories','asset_master','asset_prices','holdings','risk_profiles', 'opportunities', 'family_relationships']:
    if IS_PG:
        safe_run(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE")
    else:
        safe_run(f"DELETE FROM sqlite_sequence WHERE name='{tbl}'")

if IS_PG:
    conn.conn.commit()
else:
    conn.commit()
print("Cleared.\n")

# ── SEED REAL ADVISORS ───────────────────────────────────────────────────────
print("Seeding advisors...")

advisors_data = [
    ('Dr. Arvind Sharma',       'arvind.sharma@sanchay.io',  'Sanchay IAS', 'SEBI-RIA-2019-001', '+91-98101-11001'),
    ('Meera Krishnaswamy',      'meera.k@sanchay.io',        'Sanchay IAS', 'SEBI-RIA-2020-045', '+91-98202-22002'),
    ('Rajesh Nambiar',          'rajesh.n@sanchay.io',       'Sanchay IAS', 'SEBI-RIA-2021-089', '+91-98303-33003'),
]

advisor_ids = []
for name, email, firm, lic, phone in advisors_data:
    try:
        if IS_PG:
            uid = conn.execute('INSERT INTO users (name,email,phone,role,status,password_hash) VALUES (?,?,?,?,?,?) RETURNING user_id', (name, email, phone, 'advisor', 'active', hash_password('Sanchay@2026'))).fetchone()[0]
            aid = conn.execute('INSERT INTO advisors (user_id,firm_name,license_no) VALUES (?,?,?) RETURNING advisor_id', (uid, firm, lic)).fetchone()[0]
        else:
            cur = conn.cursor()
            cur.execute('INSERT INTO users (name,email,phone,role,status,password_hash) VALUES (?,?,?,?,?,?)', (name, email, phone, 'advisor', 'active', hash_password('Sanchay@2026')))
            uid = cur.lastrowid
            cur.execute('INSERT INTO advisors (user_id,firm_name,license_no) VALUES (?,?,?)', (uid, firm, lic))
            aid = cur.lastrowid
            
        advisor_ids.append(aid)
        print(f'  Advisor: {name} (advisor_id={aid})')
    except Exception as e:
        print(f'  Error seeding advisor {name}: {e}')

if IS_PG: conn.conn.commit()
else: conn.commit()

# ── SEED 15 REALISTIC HNI CLIENTS ───────────────────────────────────────────
print("\nSeeding clients...")

clients = [
    # (name, email, phone, dob, occupation, net_worth, income, advisor_idx, onboard_date, password)
    ('Priya Venkataraman',   'priya.v@gmail.com',        '+91-98400-11001', '1978-04-12', 'Entrepreneur / Textile Exports',    18_50_00_000,  1_20_00_000, 0, '2022-01-15', 'Priya@1234'),
    ('Rohit Malhotra',       'rohit.m@infosys.com',      '+91-98200-22001', '1982-09-23', 'VP Engineering – Infosys',          6_40_00_000,   52_00_000,   0, '2022-03-01', 'Rohit@1234'),
    ('Dr. Sunita Agarwal',   'sunita.agarwal@aiims.in',  '+91-99110-33001', '1975-02-08', 'Senior Surgeon – AIIMS Delhi',       9_20_00_000,   80_00_000,   0, '2021-11-20', 'Sunita@1234'),
    ('Karan Mehta',          'karan.mehta@tatagroup.com','+91-98000-44001', '1985-06-30', 'Director – Tata Consumer Products', 4_80_00_000,   45_00_000,   1, '2023-02-10', 'Karan@1234'),
    ('Lakshmi Iyer',         'lakshmi.iyer@hdfc.com',    '+91-97800-55001', '1980-11-14', 'CFO – HDFC Life Insurance',         12_60_00_000,  1_05_00_000, 1, '2022-06-05', 'Lakshmi@1234'),
    ('Sameer Qureshi',       'sameer.q@reliance.com',    '+91-96600-66001', '1977-03-17', 'Sr. VP Operations – Reliance Jio',  8_10_00_000,   75_00_000,   1, '2021-08-12', 'Sameer@1234'),
    ('Anjali Desai',         'anjali.desai@wipro.com',   '+91-95500-77001', '1988-07-25', 'Product Head – Wipro AI',           3_20_00_000,   38_00_000,   2, '2023-07-01', 'Anjali@1234'),
    ('Vikram Singh Rathore', 'vikram.sr@gmail.com',      '+91-94400-88001', '1970-01-05', 'Real Estate Developer – Pune',      32_00_00_000,  2_40_00_000, 2, '2020-09-15', 'Vikram@1234'),
    ('Dr. Neha Kulkarni',    'neha.k@manipalhospital.in','+91-93300-99001', '1983-12-19', 'Oncologist – Manipal Health',       5_70_00_000,   60_00_000,   2, '2022-10-30', 'Neha@1234'),
    ('Arjun Nair',           'arjun.nair@zomato.com',    '+91-92200-10001', '1991-05-04', 'Head of Growth – Zomato',           1_80_00_000,   28_00_000,   0, '2024-01-20', 'Arjun@1234'),
    ('Kavitha Subramaniam',  'kavitha.s@gmail.com',      '+91-91100-21001', '1968-08-29', 'Retired IAS Officer (Ex-Secretary)', 22_00_00_000,  15_00_000,   1, '2021-03-18', 'Kavitha@1234'),
    ('Rahul Bhatia',         'rahul.b@indigo.com',       '+91-90000-32001', '1979-10-11', 'Co-founder & CEO – IndiGo Airlines', 85_00_00_000,  5_00_00_000, 0, '2020-01-05', 'Rahul@1234'),
    ('Shreya Kapoor',        'shreya.k@swiggy.com',      '+91-88900-43001', '1993-03-22', 'VP Marketing – Swiggy',             2_40_00_000,   32_00_000,   2, '2024-04-15', 'Shreya@1234'),
    ('Mohan Lal Gupta',      'mohan.gupta@gmail.com',    '+91-87800-54001', '1965-07-07', 'Jewellery Business Owner – Jaipur', 28_00_00_000,  1_80_00_000, 1, '2019-06-01', 'Mohan@1234'),
    ('Nandita Rao',          'nandita.rao@ola.com',      '+91-86700-65001', '1986-04-18', 'CTO – Ola Electric',                7_50_00_000,   90_00_000,   2, '2023-11-10', 'Nandita@1234'),
]

client_ids = []
client_user_ids = []
client_advisor_ids_map = []  # advisor_id per client

for i, (name, email, phone, dob, occ, nw, income, adv_idx, onboard, pwd) in enumerate(clients):
    try:
        aid = advisor_ids[adv_idx] if adv_idx < len(advisor_ids) else advisor_ids[0]
        fee_bps = 75 if nw >= 150000000 else 100 if nw >= 80000000 else 125
        
        if IS_PG:
            uid = conn.execute('INSERT INTO users (name,email,phone,role,status,password_hash) VALUES (?,?,?,?,?,?) RETURNING user_id', (name, email, phone, 'client', 'active', hash_password(pwd))).fetchone()[0]
            cid = conn.execute('INSERT INTO clients (user_id,advisor_id,dob,income,net_worth,occupation,onboarding_date,advisory_fee_bps) VALUES (?,?,?,?,?,?,?,?) RETURNING client_id', (uid, aid, dob, income, nw, occ, onboard, fee_bps)).fetchone()[0]
        else:
            cur = conn.cursor()
            cur.execute('INSERT INTO users (name,email,phone,role,status,password_hash) VALUES (?,?,?,?,?,?)', (name, email, phone, 'client', 'active', hash_password(pwd)))
            uid = cur.lastrowid
            cur.execute('INSERT INTO clients (user_id,advisor_id,dob,income,net_worth,occupation,onboarding_date,advisory_fee_bps) VALUES (?,?,?,?,?,?,?,?)', (uid, aid, dob, income, nw, occ, onboard, fee_bps))
            cid = cur.lastrowid
            
        client_ids.append(cid)
        client_user_ids.append(uid)
        client_advisor_ids_map.append(aid)
        print(f'  [{i+1:2d}] {name} → client_id={cid}, advisor_id={aid}')
    except Exception as e:
        print(f'  Error seeding {name}: {e}')
        client_ids.append(None)
        client_user_ids.append(None)
        client_advisor_ids_map.append(None)

conn.commit()

# ── GOALS ────────────────────────────────────────────────────────────────────
print("\nSeeding goals...")

goals_per_client = [
    # Priya Venkataraman – Entrepreneur
    [(1, 'Business Expansion Fund',   10_00_00_000, '2027-03-31', 'High',   'On Track'),
     (1, 'Children\'s Education',      2_50_00_000,  '2030-06-30', 'Medium', 'On Track'),
     (1, 'Retirement Corpus',         25_00_00_000, '2038-04-12', 'High',   'On Track')],
    # Rohit Malhotra – IT VP
    [(2, 'Home Purchase – Bangalore',  1_80_00_000,  '2025-12-31', 'High',   'At Risk'),
     (2, 'Retirement Corpus',          8_00_00_000,  '2042-09-23', 'High',   'On Track'),
     (2, 'International Travel Fund',  20_00_000,    '2025-06-30', 'Low',    'Completed')],
    # Dr. Sunita Agarwal – Surgeon
    [(3, 'Retirement Corpus',          15_00_00_000, '2035-02-08', 'High',   'On Track'),
     (3, 'Daughter\'s Wedding Fund',   1_00_00_000,  '2028-01-01', 'Medium', 'On Track'),
     (3, 'Charitable Trust Setup',     2_00_00_000,  '2026-12-31', 'Medium', 'At Risk')],
    # Karan Mehta – Tata Director
    [(4, 'Second Home – Goa',          3_00_00_000,  '2026-06-30', 'High',   'Behind'),
     (4, 'Child Education – IVY League',1_50_00_000, '2032-08-01', 'High',   'On Track')],
    # Lakshmi Iyer – CFO
    [(5, 'Early Retirement at 50',     20_00_00_000, '2030-11-14', 'High',   'On Track'),
     (5, 'Parents\' Healthcare Fund',  50_00_000,    '2025-12-31', 'High',   'On Track')],
    # Sameer Qureshi – Reliance VP
    [(6, 'Own a Startup',              5_00_00_000,  '2027-01-01', 'High',   'On Track'),
     (6, 'Retirement Corpus',          12_00_00_000, '2037-03-17', 'High',   'On Track')],
    # Anjali Desai – Wipro
    [(7, 'Home Purchase – Hyderabad',  1_20_00_000,  '2026-03-31', 'High',   'On Track'),
     (7, 'Emergency Corpus',           30_00_000,    '2025-09-30', 'Medium', 'Completed')],
    # Vikram Singh Rathore – Real Estate
    [(8, 'Commercial Complex – Pune',  50_00_00_000, '2026-12-31', 'High',   'On Track'),
     (8, 'Family Office Setup',        10_00_00_000, '2028-01-01', 'High',   'On Track'),
     (8, 'Son\'s MBA – USA',           1_00_00_000,  '2026-08-01', 'High',   'At Risk')],
    # Dr. Neha Kulkarni – Oncologist
    [(9, 'Private Clinic Setup',       3_50_00_000,  '2027-06-30', 'High',   'On Track'),
     (9, 'Retirement Corpus',          8_00_00_000,  '2043-12-19', 'Medium', 'On Track')],
    # Arjun Nair – Zomato
    [(10,'ESOP Liquidation Strategy',  2_00_00_000,  '2026-12-31', 'High',   'On Track'),
     (10,'First Home – Mumbai',        1_50_00_000,  '2028-05-04', 'High',   'On Track')],
    # Kavitha Subramaniam – Retired IAS
    [(11,'Estate Planning & Will',     22_00_00_000, '2025-12-31', 'High',   'At Risk'),
     (11,'Grandchildren Education',    2_00_00_000,  '2035-01-01', 'Medium', 'On Track'),
     (11,'Pilgrimage & Travel',        25_00_000,    '2025-10-01', 'Low',    'On Track')],
    # Rahul Bhatia – IndiGo CEO
    [(12,'Family Office Consolidation',1_00_00_00_000,'2026-01-01','High',   'On Track'),
     (12,'Private Jet – Fractional',   15_00_00_000, '2025-12-31', 'High',   'At Risk'),
     (12,'Philanthropy Corpus',        20_00_00_000, '2030-01-01', 'Medium', 'On Track')],
    # Shreya Kapoor – Swiggy VP
    [(13,'Home Purchase – Bangalore',  90_00_000,    '2026-12-31', 'High',   'On Track'),
     (13,'Emergency Corpus',           20_00_000,    '2025-08-31', 'Medium', 'On Track')],
    # Mohan Lal Gupta – Jeweller
    [(14,'Business Succession Planning',5_00_00_000, '2026-06-30', 'High',   'On Track'),
     (14,'Retirement – Varanasi Home', 1_50_00_000,  '2025-07-07', 'Medium', 'Completed'),
     (14,'Grandchildren Trust',        10_00_00_000, '2035-01-01', 'High',   'On Track')],
    # Nandita Rao – Ola CTO
    [(15,'ESOP Monetisation',          5_00_00_000,  '2026-09-30', 'High',   'On Track'),
     (15,'Higher Education – US/UK',   1_00_00_000,  '2029-04-18', 'Medium', 'On Track')],
]

for i, goal_list in enumerate(goals_per_client):
    cid = client_ids[i] if i < len(client_ids) else None
    if not cid: continue
    for (ci, goal_type, target_amount, target_date, priority, status) in goal_list:
        try:
            conn.execute(
                'INSERT INTO goals (client_id,goal_type,target_amount,target_date,priority,status) VALUES (?,?,?,?,?,?)',
                (cid, goal_type, target_amount, target_date, priority, status)
            )
        except Exception as e:
            print(f'  Goal error for client {cid}: {e}')

if IS_PG: conn.conn.commit()
else: conn.commit()
print(f'  Goals seeded.')

# ── PORTFOLIOS (aggregated summary) ─────────────────────────────────────────
print("\nSeeding portfolios...")

portfolios = [
    # (client_idx, equity%, debt%, gold%, re%, cash%, total_value, invested_value)
    (0,  55, 25, 10, 5,  5,  16_80_00_000, 13_20_00_000),
    (1,  45, 35, 10, 0, 10,   5_80_00_000,  4_90_00_000),
    (2,  40, 40, 15, 0,  5,   8_40_00_000,  7_10_00_000),
    (3,  50, 30,  5, 5, 10,   4_20_00_000,  3_80_00_000),
    (4,  35, 45, 10, 5,  5,  11_50_00_000,  9_80_00_000),
    (5,  60, 20, 10, 0, 10,   7_40_00_000,  5_90_00_000),
    (6,  55, 30,  5, 0, 10,   2_80_00_000,  2_40_00_000),
    (7,  30, 20,  5,40,  5,  28_00_00_000, 18_50_00_000),
    (8,  45, 35, 10, 0, 10,   5_10_00_000,  4_40_00_000),
    (9,  70, 15,  5, 0, 10,   1_60_00_000,  1_30_00_000),
    (10, 20, 60, 15, 0,  5,  20_00_00_000, 17_50_00_000),
    (11, 40, 30,  5,20,  5,  77_00_00_000, 52_00_00_000),
    (12, 60, 20, 10, 0, 10,   2_10_00_000,  1_80_00_000),
    (13, 35, 35, 15,10,  5,  25_00_00_000, 19_00_00_000),
    (14, 55, 25, 10, 0, 10,   6_80_00_000,  5_40_00_000),
]

for (cidx, eq, dt, gd, re, cs, tv, iv) in portfolios:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    if not cid: continue
    try:
        conn.execute(
            'INSERT INTO portfolios (client_id, total_value) VALUES (?,?)',
            (cid, tv)
        )
    except Exception as e:
        print(f'  Portfolio error client {cid}: {e}')

if IS_PG: conn.conn.commit()
else: conn.commit()
print('  Portfolios seeded.')

# ── TASKS ────────────────────────────────────────────────────────────────────
print("\nSeeding tasks...")

from datetime import datetime
today = date.today()
d = lambda days: (today + timedelta(days=days)).isoformat()

tasks_data = [
    # (client_idx, advisor_idx, task_type, priority, due_date, status)
    (0,  0, 'Annual Portfolio Review – Priya Venkataraman',         'High',   d(7),   'Pending'),
    (0,  0, 'Rebalance equity from 55% to 50%',                     'Medium', d(14),  'Pending'),
    (1,  0, 'Home loan pre-payment analysis – Rohit Malhotra',      'High',   d(-3),  'Pending'),  # overdue
    (1,  0, 'Review term insurance coverage adequacy',              'High',   d(5),   'Pending'),
    (2,  0, 'Trust fund documentation – Dr. Sunita Agarwal',       'High',   d(10),  'Pending'),
    (2,  0, 'Tax harvesting – FY2025-26 Q2 review',                'Medium', d(20),  'Pending'),
    (3,  1, 'Second home down payment planning – Karan Mehta',     'High',   d(-7),  'Pending'),  # overdue
    (3,  1, 'NPS additional contribution – Section 80CCD',         'Low',    d(30),  'Pending'),
    (4,  1, 'Debt restructuring – move 10% to SDL bonds',          'High',   d(5),   'Pending'),
    (4,  1, 'Review healthcare parents\' cover – Lakshmi Iyer',    'High',   d(3),   'Pending'),
    (5,  1, 'ELSS SIP increase post salary revision – Sameer Q',   'Medium', d(15),  'Pending'),
    (6,  2, 'Mutual fund SIP setup – Anjali Desai',                'High',   d(2),   'Pending'),
    (7,  2, 'Commercial project IRR analysis – Vikram Rathore',    'High',   d(-2),  'Pending'),  # overdue
    (7,  2, 'Overseas investment compliance check – FEMA',         'High',   d(8),   'Pending'),
    (8,  2, 'Clinic loan pre-qualification – Dr. Neha Kulkarni',   'High',   d(12),  'Pending'),
    (9,  0, 'ESOP vesting calendar review – Arjun Nair',           'High',   d(1),   'Pending'),
    (10, 1, 'Will drafting & estate planning – Kavitha S.',        'High',   d(-5),  'Pending'),  # overdue
    (10, 1, 'Fixed deposit laddering strategy',                    'Medium', d(25),  'Pending'),
    (11, 0, 'Family office structure review – Rahul Bhatia',       'Critical',d(3),  'Pending'),
    (11, 0, 'Private equity allocation review',                    'High',   d(7),   'Pending'),
    (12, 2, 'Home loan eligibility check – Shreya Kapoor',        'High',   d(6),   'Pending'),
    (13, 1, 'Business succession legal framework – Mohan Gupta',  'High',   d(-1),  'Pending'),  # overdue
    (13, 1, 'FY2025 tax filing support – capital gains',          'High',   d(10),  'Pending'),
    (14, 2, 'ESOP exercise strategy – Nandita Rao',               'High',   d(4),   'Pending'),
    (14, 2, 'US education fund FX hedging strategy',              'Medium', d(20),  'Pending'),
]

for (cidx, aidx, task_type, priority, due_date, status) in tasks_data:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    aid = advisor_ids[aidx] if aidx < len(advisor_ids) else advisor_ids[0]
    if not cid: continue
    
    # Derive category
    tt_lower = task_type.lower()
    if 'review' in tt_lower: category = 'Portfolio Review'
    elif 'tax' in tt_lower: category = 'Tax Strategy'
    elif 'kyc' in tt_lower or 'document' in tt_lower: category = 'KYC Collection'
    elif 'call' in tt_lower: category = 'Call Client'
    elif 'loan' in tt_lower or 'eligibility' in tt_lower: category = 'Financial Planning'
    else: category = 'General'
    
    desc = f"Action Required: {task_type}. Coordinate with the client as necessary to execute this task."
    
    try:
        conn.execute(
            'INSERT INTO tasks (advisor_id,client_id,task_type,priority,due_date,status,owner_id,category,description) VALUES (?,?,?,?,?,?,?,?,?)',
            (aid, cid, task_type, priority, due_date, status, aid, category, desc)
        )
    except Exception as e:
        print(f'  Task error: {e}')

if IS_PG: conn.conn.commit()
else: conn.commit()
print(f'  Tasks seeded.')

# ── TRANSACTIONS ─────────────────────────────────────────────────────────────
print("\nSeeding transactions...")

asset_rows = conn.execute('SELECT asset_id FROM asset_master LIMIT 20').fetchall()
asset_ids  = [r['asset_id'] for r in asset_rows] or [1,2,3,4,5]

txn_types = ['BUY','BUY','BUY','SELL','SIP','SIP']
def rdate(days_ago): return (today - timedelta(days=days_ago)).isoformat()

sample_txns = [
    (0,  rdate(2),   'SIP',  500,   450,    2),
    (0,  rdate(30),  'BUY',  200,   1250,   1),
    (0,  rdate(60),  'SELL', 100,   1380,   3),
    (1,  rdate(5),   'SIP',  300,   520,    2),
    (1,  rdate(45),  'BUY',  50,    2300,   4),
    (2,  rdate(10),  'SIP',  1000,  185,    2),
    (2,  rdate(20),  'BUY',  100,   3100,   5),
    (3,  rdate(3),   'SIP',  200,   460,    2),
    (3,  rdate(90),  'BUY',  500,   420,    1),
    (4,  rdate(7),   'SIP',  2000,  220,    2),
    (4,  rdate(15),  'SELL', 300,   3400,   3),
    (5,  rdate(1),   'BUY',  1000,  380,    1),
    (6,  rdate(14),  'SIP',  200,   510,    2),
    (7,  rdate(30),  'BUY',  10,    85000,  4),
    (7,  rdate(60),  'SELL', 5,     92000,  4),
    (8,  rdate(4),   'SIP',  500,   290,    2),
    (9,  rdate(2),   'BUY',  5000,  145,    1),
    (10, rdate(20),  'SIP',  3000,  180,    2),
    (11, rdate(5),   'BUY',  100,   25000,  5),
    (12, rdate(8),   'SIP',  200,   490,    2),
    (13, rdate(3),   'BUY',  1000,  340,    1),
    (13, rdate(45),  'SELL', 500,   720,    3),
    (14, rdate(6),   'SIP',  500,   410,    2),
]

for (cidx, txn_date, txn_type, qty, price, aid_idx) in sample_txns:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    if not cid: continue
    a_id = asset_ids[cidx % len(asset_ids)] if asset_ids else 1
    try:
        conn.execute(
            'INSERT INTO transactions (client_id,asset_id,txn_type,quantity,price,txn_date) VALUES (?,?,?,?,?,?)',
            (cid, a_id, txn_type, qty, price, txn_date)
        )
    except Exception as e:
        print(f'  Txn error for client {cid}: {e}')

if IS_PG: conn.conn.commit()
else: conn.commit()
print('  Transactions seeded.')

# ── NOTIFICATIONS (pending consent requests) ─────────────────────────────────
print("\nSeeding notifications...")

notif_data = [
    (0,  advisor_ids[0], 'portfolio_change',
     'Portfolio Rebalancing Alert: Your equity allocation has been increased from 50% to 55% (₹84 Lakhs additional equity exposure) following strong Q1 FY26 earnings momentum. Please review and confirm your agreement.'),

    (3,  advisor_ids[1], 'portfolio_change',
     'Portfolio Update: ₹50 Lakhs moved from liquid funds to HDFC Flexi Cap Fund (SIP ₹2L/month) to align with your Second Home goal timeline of Dec 2026. Action required.'),

    (7,  advisor_ids[2], 'portfolio_change',
     'Significant Transaction: Sold 5 units of Commercial Land (Pune, Wakad plot) at ₹92,000/sq.ft. Net proceeds of ₹4.6 Cr credited to your portfolio. Tax implications being assessed. Please confirm.'),

    (10, advisor_ids[1], 'meeting_minutes',
     'Meeting Minutes – Estate Planning Session (Jun 1, 2026): We discussed drafting a registered Will, setting up a Private Family Trust, and nominating executors. Action items: (1) Share property documents by Jun 15. (2) Legal counsel appointment on Jun 20. Please confirm receipt and agreement.'),

    (11, advisor_ids[0], 'portfolio_change',
     'Family Office Restructuring: Proposed allocation of ₹25 Cr into Category II AIF (Edelweiss Special Opportunities Fund) as part of diversification. This is a 36-month lock-in instrument. Please review the term sheet and indicate your consent.'),

    (2,  advisor_ids[0], 'meeting_minutes',
     'Meeting Minutes – Charitable Trust Review (May 28, 2026): Discussed structure of corpus – ₹2 Cr earmarked for charitable trust corpus. Proposed trustees: Dr. Sunita Agarwal, CA Ravi Shankar, NGO representative. Registration process to begin Jul 2026. Please confirm.'),
]

for (cidx, aid, ntype, content) in notif_data:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    if not cid: continue
    try:
        conn.execute(
            'INSERT INTO notifications (client_id, advisor_id, type, content, consent_status) VALUES (?,?,?,?,?)',
            (cid, aid, ntype, content, 'pending')
        )
    except Exception as e:
        print(f'  Notif error for client {cid}: {e}')

# Some already-resolved notifications
resolved = [
    (1,  advisor_ids[0], 'portfolio_change', 'agree',
     'SIP increased from ₹20,000 to ₹50,000/month in Parag Parikh Flexi Cap Fund effective April 2026. This aligns with your revised savings rate post increment.'),
    (4,  advisor_ids[1], 'portfolio_change', 'agree',
     'Switched ₹30L from short-term FDs (5.8% p.a.) to REC Tax-Free Bonds (6.75% p.a.) to optimise post-tax yield on debt allocation.'),
    (5,  advisor_ids[1], 'portfolio_change', 'disagree',
     'Proposed shift of ₹40L into International Fund of Funds. Client preferred to maintain India-only allocation for now.'),
]

for (cidx, aid, ntype, status, content) in resolved:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    if not cid: continue
    try:
        conn.execute(
            'INSERT INTO notifications (client_id, advisor_id, type, content, consent_status) VALUES (?,?,?,?,?)',
            (cid, aid, ntype, content, status)
        )
    except Exception as e:
        print(f'  Notif error: {e}')

conn.commit()
print('  Notifications seeded.')

# ── MEETING MINUTES ──────────────────────────────────────────────────────────
print("\nSeeding meeting minutes...")

minutes_data = [
    (0, advisor_ids[0], '2026-04-15',
     'Annual Review',
     'Reviewed FY2025-26 performance. Portfolio returned 18.4% vs Nifty 14.2%. Discussed business expansion into UAE market. Agreed to increase equity exposure. Reviewed insurance cover – recommended enhancing term cover by ₹5 Cr.',
     '1. Increase SIP by ₹50K/month from June\n2. Get additional term cover quote from LIC\n3. Explore NRI account for UAE operations'),

    (3, advisor_ids[1], '2026-05-10',
     'Goal Review – Second Home Purchase',
     'Discussed timeline for Goa property purchase. Current corpus: ₹1.2 Cr. Gap: ₹1.8 Cr. Revised SIP to close gap by Q3 2026. Discussed home loan pre-approval from HDFC at 8.9% p.a.',
     '1. Apply for pre-approved home loan\n2. Increase SIP to ₹2L/month\n3. Visit property shortlist in Goa – Jun 2026'),

    (10, advisor_ids[1], '2026-06-01',
     'Estate Planning & Will Discussion',
     'Comprehensive estate planning session. Assets: Flat in Chennai (₹4Cr), FDs (₹8Cr), Mutual Funds (₹6Cr), Gold (₹4Cr). Discussed Private Family Trust vs direct will. Recommended engaging M/s Shardul Amarchand law firm for Will drafting.',
     '1. Share property documents by Jun 15\n2. Legal appointment on Jun 20\n3. Review existing nominations on all assets'),

    (11, advisor_ids[0], '2026-05-20',
     'Family Office Strategy 2026-27',
     'Rahul Bhatia reviewed family office structure. Current AUM: ₹85 Cr. Proposed: ₹25Cr into AIF (Category II), ₹15Cr in direct equity, ₹20Cr in real assets, balance in fixed income. Discussed offshore trust setup in Singapore for international assets.',
     '1. Review Edelweiss AIF term sheet\n2. Engage Singapore trust lawyer\n3. Board resolution for Bhatia Family Trust'),
]

for (cidx, aid, mdate, agenda, discussion, actions) in minutes_data:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    if not cid: continue
    try:
        conn.execute(
            'INSERT INTO meeting_minutes (client_id,advisor_id,meeting_date,agenda,discussion,action_items) VALUES (?,?,?,?,?,?)',
            (cid, aid, mdate, agenda, discussion, actions)
        )
    except Exception as e:
        print(f'  Minutes error for client {cid}: {e}')

conn.commit()
print('  Meeting minutes seeded.')

# ── SEED ASSET MASTER DATA ───────────────────────────────────────────────────
print("\nSeeding asset categories and master...")
categories = [
    (1, 'Equity'),
    (2, 'Debt'),
    (3, 'Gold'),
    (4, 'Cash')
]
for cid, name in categories:
    conn.execute('INSERT INTO asset_categories (category_id, category_name) VALUES (?, ?)', (cid, name))

assets = [
    (1, 'INFY', 1, 'INR', 'Medium', 'High', 'Technology', 'Large Cap', 'Growth'),
    (2, 'TCS', 1, 'INR', 'Medium', 'High', 'Technology', 'Large Cap', 'Growth'),
    (3, 'RELIANCE', 1, 'INR', 'Medium', 'High', 'Energy', 'Large Cap', 'Value'),
    (4, 'HDFCBANK', 1, 'INR', 'Medium', 'High', 'Finance', 'Large Cap', 'Quality'),
    (5, 'NIPPON_LIQUID', 2, 'INR', 'Low', 'High', 'Fixed Income', 'Large Cap', 'Yield'),
    (6, 'SBI_GOLD', 3, 'INR', 'Low', 'High', 'Alternative', 'Large Cap', 'Inflation')
]
for aid, name, cat_id, cur_code, risk, liq, sector, mcap, factor in assets:
    conn.execute('INSERT INTO asset_master (asset_id, asset_name, category_id, base_currency, risk_level, liquidity_type, sector, market_cap_category, investment_factor) VALUES (?,?,?,?,?,?,?,?,?)',
                 (aid, name, cat_id, cur_code, risk, liq, sector, mcap, factor))

prices = [
    (1, 1500.0, '2026-06-01 16:00:00', 'NSE'),
    (2, 3800.0, '2026-06-01 16:00:00', 'NSE'),
    (3, 2400.0, '2026-06-01 16:00:00', 'NSE'),
    (4, 1600.0, '2026-06-01 16:00:00', 'NSE'),
    (5, 1000.0, '2026-06-01 16:00:00', 'NAV'),
    (6, 6500.0, '2026-06-01 16:00:00', 'NAV')
]
for asset_id, price, pdate, src in prices:
    conn.execute('INSERT INTO asset_prices (asset_id, price, price_date, source) VALUES (?,?,?,?)',
                 (asset_id, price, pdate, src))

print("Asset categories and master seeded.")

# ── SEED RISK PROFILES & HOLDINGS ─────────────────────────────────────────────
print("\nSeeding risk profiles and holdings...")
for idx, cid in enumerate(client_ids):
    if not cid: continue
    # 1. Risk Profile
    risk_score = random.randint(40, 75)
    risk_cat = 'Balanced' if risk_score < 60 else 'Aggressive'
    conn.execute('''
        INSERT INTO risk_profiles (client_id, risk_score, risk_category, liquidity_score, investment_horizon, last_updated)
        VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)
    ''', (cid, risk_score, risk_cat, random.randint(60, 90), random.randint(5, 15)))

    # 2. Holdings based on portfolio allocation and portfolio total_value
    # Let's get total_value for client
    row = conn.execute('SELECT portfolio_id, total_value FROM portfolios WHERE client_id = ?', (cid,)).fetchone()
    if not row: continue
    port_id = row['portfolio_id']
    tot_val = float(row['total_value'])

    # Get client portfolios allocation weights
    port_weight = portfolios[idx] if idx < len(portfolios) else (idx, 50, 30, 10, 0, 10, tot_val, tot_val)
    eq_w = port_weight[1]
    dt_w = port_weight[2]
    gd_w = port_weight[3]
    re_w = port_weight[4]
    cs_w = port_weight[5]
    
    # Insert Holdings
    # Equity split among INFY(1), TCS(2), RELIANCE(3), HDFCBANK(4)
    eq_each_val = (eq_w / 100.0 * tot_val) / 4.0
    for aid, cur_price in [(1, 1500.0), (2, 3800.0), (3, 2400.0), (4, 1600.0)]:
        qty = eq_each_val / cur_price
        avg_buy = cur_price * 0.9
        conn.execute('''
            INSERT INTO holdings (portfolio_id, asset_id, quantity, avg_buy_price, allocation_percent)
            VALUES (?,?,?,?,?)
        ''', (port_id, aid, qty, avg_buy, eq_w / 4.0))

    # Debt (NIPPON_LIQUID - 5)
    dt_val = (dt_w / 100.0 * tot_val)
    qty_dt = dt_val / 1000.0
    conn.execute('''
        INSERT INTO holdings (portfolio_id, asset_id, quantity, avg_buy_price, allocation_percent)
        VALUES (?,?,?,?,?)
    ''', (port_id, 5, qty_dt, 1000.0, dt_w))

    # Gold (SBI_GOLD - 6)
    gd_val = (gd_w / 100.0 * tot_val)
    qty_gd = gd_val / 6500.0
    conn.execute('''
        INSERT INTO holdings (portfolio_id, asset_id, quantity, avg_buy_price, allocation_percent)
        VALUES (?,?,?,?,?)
    ''', (port_id, 6, qty_gd, 6000.0, gd_w))

    # 3. Write portfolio aggregates for analytics matching the holdings we just added!
    re_val = (re_w / 100.0 * tot_val)
    conn.execute('''
        INSERT INTO portfolio_aggregates (client_id, total_value, equity_value, debt_value, mf_value, insurance_value, alternative_value, last_computed)
        VALUES (?,?,?,?,0,0,?,CURRENT_TIMESTAMP)
    ''', (cid, tot_val, eq_each_val * 4.0, dt_val, re_val))

    # 4. Generate monthly historical snapshots (last 12 months)
    for m in range(12):
        snap_date = (date.today() - timedelta(days=(11 - m) * 30)).strftime('%Y-%m-%d')
        # Simulate value growth
        perf_factor = 0.88 + (m / 11.0) * 0.12 + random.uniform(-0.015, 0.015)
        if m == 11:
            perf_factor = 1.0  # Align with today's value
        v_total = tot_val * perf_factor
        v_eq = eq_each_val * 4.0 * perf_factor
        v_dt = dt_val * perf_factor
        v_gd = (gd_w / 100.0 * tot_val) * perf_factor
        v_cs = (cs_w / 100.0 * tot_val) * perf_factor
        
        conn.execute('''
            INSERT INTO portfolio_historical_snapshots (client_id, snapshot_date, total_value, equity_value, debt_value, gold_value, cash_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (cid, snap_date, v_total, v_eq, v_dt, v_gd, v_cs))

    # 5. Generate client-specific portfolio events
    events = [
        (1, 'Dividend', 'INFY', (date.today() - timedelta(days=2)).strftime('%Y-%m-%d'), 3, 1.2, 'Reinvest dividend', 'Infosys announced a final dividend of Rs 20/share.'),
        (4, 'Earnings', 'HDFCBANK', (date.today() - timedelta(days=5)).strftime('%Y-%m-%d'), 4, 1.1, 'Maintain finance sector allocation', 'HDFC Bank reported strong Net Interest Income growth of 12% YoY, beating estimates.'),
        (5, 'RBI Policy', 'NIPPON_LIQUID', (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'), 4, 1.0, 'Retain debt duration', 'RBI MPC voted to hold repo rate at 6.50%. This favors our fixed income duration positioning.'),
        (3, 'Corporate Actions', 'RELIANCE', (date.today() - timedelta(days=10)).strftime('%Y-%m-%d'), 5, 1.3, 'Participate in buyback', 'Reliance announced a capital restructuring / stock buyback proposal to optimize leverage.')
    ]
    for asset_id, etype, sec_name, edate, sev, sens, action, text in events:
        conn.execute('''
            INSERT INTO portfolio_events (client_id, asset_id, event_type, security_name, event_date, severity, sensitivity, recommended_action, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cid, asset_id, etype, sec_name, edate, sev, sens, action, text))

print("Holdings, risk profiles, portfolio aggregates, historical snapshots, and events seeded.")

# ── SEED OPPORTUNITIES & HOUSEHOLDS (PHASE 1 ADVISOR OS) ────────────────────
print("\nSeeding opportunities and family relationships...")

# 1. Opportunities Seeding
opp_data = [
    # client_idx, type, title, expected_benefit, revenue_potential, client_impact, priority, status
    (0, 'Idle Cash', '₹84L Low-Yield Savings Deployment', 'Earns additional 4.2% yield p.a. (₹3.5L/yr)', 42000, 'Deploys idle bank savings to Nippon Liquid yield fund.', 'Medium', 'Open'),
    (0, 'Underfunded Goal', "SIP Gap for Children's Education", 'Raises goal success probability from 72% to 88%', 15000, 'Increases monthly SIP commitment by ₹45,000 to bridge gap.', 'High', 'Open'),
    (0, 'Tax Harvesting', 'Q2 Equity Long Term Loss Offset', 'Reduces tax liability by ₹1,45,000 in capital gains', 0, 'Realize underperforming tech asset losses to offset gains.', 'Low', 'Open'),
    (1, 'Insurance Gap', 'Term Life Coverage Shortfall', 'Provides 10x household income cover protection', 12000, 'Onboard ₹3.0 Cr term life policy matching income benchmarks.', 'High', 'Open'),
    (1, 'Idle Cash', 'Excess Cash Sweep opportunity', 'Earns 6.8% return on temporary treasury float', 15000, 'Deploy ₹30L idle cash to high-grade money market instruments.', 'Medium', 'Open'),
    (2, 'Portfolio Optimization', 'Excess Finance Sector Concentration', 'Lowers portfolio standard deviation by 1.2%', 20000, 'Trim HDFCBANK overweight by 5.2% and re-allocate to gold.', 'High', 'Open'),
    (3, 'Underfunded Goal', 'Retirement Corpus SIP shortfall', 'Closes ₹82L retirement gap before target year', 10000, 'Suggested SIP increase of ₹18,000/mo to keep retirement on track.', 'Medium', 'Open')
]

for (cidx, otype, title, benefit, rev, impact, prio, status) in opp_data:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    if not cid: continue
    conn.execute('''
        INSERT INTO opportunities (client_id, type, title, expected_benefit, revenue_potential, client_impact, priority, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cid, otype, title, benefit, rev, impact, prio, status))

# 2. Family Relationships Seeding
fam_data = [
    # client_idx, related_client_idx, relation_type, family_name
    (0, 1, 'Spouse', 'Venkataraman & Malhotra Family Trust'),
    (1, 0, 'Spouse', 'Venkataraman & Malhotra Family Trust'),
    (2, 3, 'Sibling', 'Agarwal Sibling Trust'),
    (3, 2, 'Sibling', 'Agarwal Sibling Trust')
]

for (cidx, rcidx, rtype, fname) in fam_data:
    cid = client_ids[cidx] if cidx < len(client_ids) else None
    rcid = client_ids[rcidx] if rcidx < len(client_ids) else None
    if not cid or not rcid: continue
    conn.execute('''
        INSERT INTO family_relationships (client_id, related_client_id, relation_type, family_name)
        VALUES (?, ?, ?, ?)
    ''', (cid, rcid, rtype, fname))

print("Opportunities and family relationships successfully seeded.")

if not IS_PG:
    conn.execute('PRAGMA foreign_keys=ON')
    
if IS_PG:
    conn.conn.commit()
    conn_gen.__exit__(None, None, None)
else:
    conn.commit()
    conn.close()

print('\n' + '='*60)
print('SEED COMPLETE -- SANCHAY IAS is ready with realistic data')
print('='*60)
print(f'  Advisors:          {len(advisor_ids)}')
print(f'  Clients:           {len([x for x in client_ids if x])}')
print(f'  Goals:             {sum(len(g) for g in goals_per_client)}')
print(f'  Tasks:             {len(tasks_data)}')
print(f'  Transactions:      {len(sample_txns)}')
print(f'  Notifications:     {len(notif_data) + len(resolved)}')
print(f'  Meeting Minutes:   {len(minutes_data)}')
