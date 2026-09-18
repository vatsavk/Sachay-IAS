import re
import subprocess
import os

def check():
    path = r'e:\SANCHAY\Sanchay_IAS\frontend\client_portal.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all <script> blocks (excluding external ones)
    scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
    
    if not scripts:
        print("No inline scripts found!")
        return
        
    print(f"Found {len(scripts)} inline script block(s).")
    
    # Save the main inline script to a temp file
    temp_path = r'e:\SANCHAY\Sanchay_IAS\scratch\temp_index.js'
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(scripts[0])
        
    print("Running syntax check on extracted script...")
    res = subprocess.run(['node', '-c', temp_path], capture_output=True, text=True)
    
    if res.returncode == 0:
        print("Syntax is VALID!")
    else:
        print("Syntax is INVALID!")
        print(res.stderr)

if __name__ == '__main__':
    check()
