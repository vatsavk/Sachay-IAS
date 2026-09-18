import sqlite3

conn = sqlite3.connect(r'E:\SANCHAY\Sanchay_IAS\sanchay_local.db')
conn.row_factory = sqlite3.Row

tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print('TABLES:', [t[0] for t in tables])

for t in ['clients','users','advisors','goals','tasks','portfolios','transactions','notifications','meeting_minutes']:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'{t.upper()}: {cnt}')
    except Exception as e:
        print(f'{t.upper()}: ERROR - {e}')

print()
print('--- ADVISORS ---')
for r in conn.execute('SELECT a.advisor_id, u.name, u.email FROM advisors a JOIN users u ON a.user_id=u.user_id').fetchall():
    print(dict(r))

conn.close()
