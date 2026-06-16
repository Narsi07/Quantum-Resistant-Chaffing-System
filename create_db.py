"""Test PostgreSQL connection with different passwords."""
import psycopg2

passwords = ['', 'admin', '1234', '12345', 'password', 'postgres123', 'root', 'narasimman', 'NARASIMMAN']

found = None
for pw in passwords:
    try:
        conn = psycopg2.connect(
            host="localhost", port=5432,
            database="postgres", user="postgres",
            password=pw,
            connect_timeout=3,
        )
        conn.close()
        found = pw
        print(f"SUCCESS! Password is: [{pw}]")
        break
    except psycopg2.OperationalError as e:
        err = str(e).strip().split('\n')[0]
        print(f"  [{pw!r}] -> {err}")

if not found:
    print("\nNone worked. Please reset your PostgreSQL password:")
    print('  Run as Administrator:')
    print('  & "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe" -U postgres')
    print('  Then type:  ALTER USER postgres PASSWORD \'postgres\';')
