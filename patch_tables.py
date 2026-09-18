import re
with open('init_local_db.py', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Find all CREATE TABLE blocks
tables = re.findall(r'CREATE TABLE\s+(\w+)\s*\((.*?)\);', sql_script, re.DOTALL)

with open('sanchay_db.py', 'r', encoding='utf-8') as f:
    db_code = f.read()

new_tables = []
for tbl_name, tbl_body in tables:
    if f'CREATE TABLE IF NOT EXISTS {tbl_name} ' not in db_code and f'CREATE TABLE IF NOT EXISTS {tbl_name}(' not in db_code:
        new_tables.append("        conn.execute('''\n            CREATE TABLE IF NOT EXISTS " + tbl_name + " (" + tbl_body + ");\n        ''')\n")

insertion_point = db_code.find('    # Ensure at least one advisor exists')
if insertion_point != -1:
    new_code = db_code[:insertion_point] + '\n'.join(new_tables) + '\n' + db_code[insertion_point:]
    with open('sanchay_db.py', 'w', encoding='utf-8') as f:
        f.write(new_code)
    print('Inserted missing tables into sanchay_db.py')
else:
    print('Insertion point not found')
