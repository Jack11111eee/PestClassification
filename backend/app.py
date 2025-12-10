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
# 你的前端地址是 http://10.61.190.21:5174，这个配置是正确的
CORS(app, resources={r"/api/*": {"origins": "http://10.61.190.21:5174"}}, supports_credentials=True)

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

# !!! 注意：蓝图冲突 !!!
# 你不能将两个不同的蓝图注册到同一个 /api/admin 前缀。
# 我暂时注释掉 user_admin_bp。你需要决定它的正确路径。
# 比如，你可以把它改成 '/api/user-management'
# app.register_blueprint(user_admin_bp, url_prefix='/api/user-management') 
# 暂时先不注册，避免覆盖掉 admin_bp 里的 /api/admin/detections 接口
# app.register_blueprint(user_admin_bp, url_prefix='/api/admin') 

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
    # 初始化管理员
    init_admin()
    
    print("🚀 Flask backend starting...")
    print("🌐 Access it from your network at: http://<YOUR_IP_ADDRESS>:5000")
    
    # !!! 关键修改 !!!
    # 必须使用 host='0.0.0.0'，这样才能从局域网访问
    app.run(host='0.0.0.0', port=5000, debug=True)

