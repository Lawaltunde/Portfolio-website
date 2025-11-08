import os
import sqlparse
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

def main():
    # Load environment variables from .env file
    dotenv_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=dotenv_path)

    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_role_key:
        print("NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in the .env file.")
        return

    supabase: Client = create_client(url, service_role_key)

    # Read the schema.sql file
    schema_path = Path(__file__).parent.parent / 'supabase_schema.sql'
    with open(schema_path, 'r') as f:
        sql_script = f.read()
    
    sql_commands = sqlparse.split(sql_script)


    # Execute the schema
    for command in sql_commands:
        if command.strip():
            try:
                supabase.rpc('execute_sql', {'sql': command}).execute()
                print(f"Successfully executed: {command.strip()}")
            except Exception as e:
                print(f"Error executing command: {command.strip()}\n{e}")

    print("Schema application process finished.")

if __name__ == "__main__":
    main()