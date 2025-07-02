import psycopg2
from psycopg2.extras import RealDictCursor
from dcm_crawler_xnat import get_subject_id

try:
    conn = psycopg2.connect(
        dbname="xnat",
        user="xnat",
        password="ozymandias",
        host="localhost",
        port="5432"
    )
    print("✅ Connected successfully!")
except Exception as e:
    print("❌ Connection failed:", e)

cur = conn.cursor(cursor_factory=RealDictCursor)

subjectid = get_subject_id('burcs', 'test001_MR_1', cur)
print(subjectid)

conn.close()