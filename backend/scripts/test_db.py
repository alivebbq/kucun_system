import psycopg2

try:
    # 尝试直接连接
    conn = psycopg2.connect(
        dbname="kucun_system",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )
    print("数据库连接成功！")
    conn.close()
except Exception as e:
    print(f"数据库连接失败: {str(e)}") 