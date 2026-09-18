import requests
import time

try:
    print("Testing /health...")
    r = requests.get("http://localhost:8001/health", timeout=5)
    print("Health:", r.json())
    
    print("Testing /clients...")
    r = requests.get("http://localhost:8001/clients", timeout=5)
    print("Clients count:", len(r.json()))
    
    print("Testing /dashboard...")
    r = requests.get("http://localhost:8001/dashboard", timeout=5)
    print("Dashboard:", r.json())
except Exception as e:
    print("Error:", e)
