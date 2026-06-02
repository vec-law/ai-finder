from db.connection import get_connection

def migrate():
    conn = get_connection()
    cur = conn.cursor()

    with open("db/schema.sql", "r") as f:
        sql = f.read()
    cur.execute(sql)

    with open("db/seeds.sql", "r") as f:
        sql = f.read()
    cur.execute(sql)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
