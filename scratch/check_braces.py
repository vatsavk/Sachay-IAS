import re

def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strip comments and strings (basic)
    content = re.sub(r'//.*', '', content)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # We won't strip strings fully, just count { and }
    open_count = content.count('{')
    close_count = content.count('}')
    
    print(f"File: {filename}")
    print(f"Open braces: {open_count}")
    print(f"Close braces: {close_count}")
    
    if open_count != close_count:
        print("MISMATCH!")
    else:
        print("MATCH!")

check_braces('app.js')
