#!/usr/bin/env python3
"""
SPCS Registry Helper - Login using JWT token from Snowflake session
"""
import subprocess
import sys
import json
import snowflake.connector
from snowflake.connector.auth import AuthByKeyPair

def main():
    connection_name = sys.argv[1] if len(sys.argv) > 1 else "my_snowflake"
    
    conn = snowflake.connector.connect(connection_name=connection_name)
    cur = conn.cursor()
    
    cur.execute("SELECT CURRENT_USER()")
    username = cur.fetchone()[0]
    
    cur.execute("SHOW IMAGE REPOSITORIES LIKE 'IMAGES' IN SCHEMA VULCAN_MATERIALS_DB.ML")
    result = cur.fetchone()
    registry_url = result[4]
    
    token = conn.rest.token
    
    conn.close()
    
    print(f"Registry: {registry_url}", file=sys.stderr)
    print(f"Username: {username}", file=sys.stderr)
    print(f"Token length: {len(token) if token else 0}", file=sys.stderr)
    
    result = subprocess.run(
        ["docker", "login", registry_url, "-u", "0sessiontoken", "--password-stdin"],
        input=token,
        capture_output=True,
        text=True
    )
    
    if "Login Succeeded" in result.stdout or result.returncode == 0:
        print("Login successful!", file=sys.stderr)
    else:
        print(f"Login output: {result.stdout} {result.stderr}", file=sys.stderr)
    
    print(registry_url)

if __name__ == "__main__":
    main()
