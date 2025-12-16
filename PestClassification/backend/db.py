import mysql.connector
from flask import g

# --- 数据库配置 ---
# 将您的配置信息集中存放在这里，方便管理
DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': "12138",
    'database': "agri",
    'charset': "utf8mb4",
    'port': 3407
}

def get_db_connection():
    """
    获取当前请求的数据库连接。
    如果连接不存在，则创建一个并存储在Flask的g对象中（一个请求内的全局变量）。
    """
    if 'db' not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db

def close_db(e=None):
    """
    关闭当前请求的数据库连接。
    这个函数会被Flask自动调用（需要在app.py中注册）。
    """
    db = g.pop('db', None)
    
    # 修正：这里是语法错误的地方，正确的写法是 'is not None'
    if db is not None:
        db.close()

# -----------------------------------------------------------------
#  下面的函数都已修改，不再手动管理连接，代码更简洁、更安全。
# -----------------------------------------------------------------

# backend/db.py (修改后的最终版本)
def save_detection(user_id, image_path, label, confidence=None):
    """保存用户检测记录，并设置状态为 'pending'"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 注意 SQL 语句的变化：移除了 is_processed, admin_uploaded，增加了 upload_status
    # 注意 VALUES 的变化：移除了 0, 0，增加了一个新的 %s
    cursor.execute(
        """
        INSERT INTO detections (user_id, image_path, label, confidence, upload_status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        # 在参数元组的最后，添加 'pending'
        (user_id, image_path, label, confidence, 'pending')
    )
    conn.commit()
    return True


def get_all_detections():
    """
    管理员获取所有检测记录（旧函数，为保持兼容而保留）。
    注意：新版admin.py中的接口不再直接调用此函数，而是在路由中直接执行SQL。
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            d.id, d.image_path, d.label, d.confidence, d.is_processed, d.admin_uploaded, d.create_at, u.username AS user
        FROM detections d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.create_at DESC
    """)
    rows = cursor.fetchall()
    # 注意：不再需要 cursor.close() 和 conn.close()
    return rows

def mark_detection_uploaded(detection_id):
    """
    管理员更新 admin_uploaded 状态（旧函数，为保持兼容而保留）。
    新版admin.py中已包含此逻辑，不再直接调用此函数。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE detections SET admin_uploaded = 1 WHERE id = %s",
        (detection_id,)
    )
    conn.commit()
    # 注意：不再需要 cursor.close() 和 conn.close()
    return True