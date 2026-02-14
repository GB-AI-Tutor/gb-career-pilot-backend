import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f'URL: {url}')
# print(f'Key: {key}...')

try:
    supabase = create_client(url, key)
    result = supabase.table('universities').select('*').limit(1).execute()
    print('✅ Supabase connection successful!')
    print(f'Data: {result.data}')
except Exception as e:
    print(f'❌ Error: {e}')