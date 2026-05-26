# backend/app.py (修正版)
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash

# --- 导入你的蓝图和数据库工具 ---
# 确保你的项目结构是正确的，能够找到这些模块
from routes.auth import auth_bp
from routes.detection import bp as detection_bp
from routes.admin import admin_bp
from routes.test import test_bp  
from routes.user_manage import user_admin_bp 
from db import get_db_connection, close_db

# =============================
# --- 1. App 初始化与核心配置 ---
# =============================
app = Flask(__name__)

# --- 配置 CORS (跨域资源共享) ---
frontend_origins = [
    origin.strip()
    for origin in os.environ.get(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5174,http://localhost:5174,http://10.61.190.21:5174"
    ).split(",")
    if origin.strip()
]
CORS(app, resources={r"/api/*": {"origins": frontend_origins}}, supports_credentials=True)

# --- 配置上传文件夹 ---
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads') # 建议放在项目根目录下的 uploads 文件夹
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- 配置 JWT ---
app.config['JWT_SECRET_KEY'] = 'your_very_secret_and_long_key_here' # 生产环境请务必修改
jwt = JWTManager(app)

# =============================
# --- 2. 注册蓝图 (Blueprints) ---
# =============================
# 关键：在每次请求结束后自动关闭数据库连接
app.teardown_appcontext(close_db)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(detection_bp, url_prefix="/api/detection")
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(test_bp, url_prefix='/api/test')

# =============================
# --- 3. 辅助函数与路由 ---
# =============================
@app.route('/')
def index():
    return jsonify({"message": "Backend running successfully!"}), 200

def init_admin():
    """初始化默认管理员账户"""
    # 使用 with app.app_context() 确保 g 对象可用
    with app.app_context():
        conn = get_db_connection()
        if conn is None:
            print("❌ 无法连接到数据库，跳过管理员初始化。")
            return
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE role='admin'")
        admins = cursor.fetchall()

        if not admins:
            print("⚙️ 未检测到管理员账户，正在创建默认管理员：admin / admin123")
            hashed_pw = generate_password_hash("admin123")
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                ("admin", hashed_pw, "admin")
            )
            conn.commit()
        else:
            print(f"✅ 检测到管理员账户：{admins[0]['username']}")

        cursor.close()
        # conn.close() 会由 teardown_appcontext 自动处理，这里可以不写

# =============================
# --- 4. 程序入口 (最关键的修改！) ---
# =============================
if __name__ == '__main__':
    # with app.app_context():
    #     print("="*80)
    #     print("[[[ Flask 应用中所有可用的 API 路由列表 ]]]")
    #     rules = []
    #     for rule in app.url_map.iter_rules():
    #         # 过滤掉 Flask 内部的 'static' 路由
    #         if rule.endpoint != 'static':
    #             # 获取路由支持的 HTTP 方法 (GET, POST, etc.)
    #             methods = ','.join(sorted(rule.methods))
    #             # 格式化输出：URL -> Endpoint (Methods)
    #             rules.append(f"{rule.rule:<40} {rule.endpoint:<20} {methods}")
        
    #     for r in sorted(rules):
    #         print(r)
    #     print("="*80)
    # 初始化管理员
    init_admin()
    
    print("🚀 Flask backend starting...")
    print("🌐 Access it from your network at: http://<YOUR_IP_ADDRESS>:5000")
    
    # !!! 关键修改 !!!
    # 必须使用 host='0.0.0.0'，这样才能从局域网访问
    app.run(host='0.0.0.0', port=5000, debug=True)

