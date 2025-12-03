# backend/app.py (完整代码)
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from routes.auth import auth_bp
from routes.detection import bp as detection_bp
from routes.admin import admin_bp
from routes.test import test_bp  
from db import get_db_connection, close_db # <-- 关键：导入 close_db
from flask_sqlalchemy import SQLAlchemy
# --- App 初始化 ---
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = os.path.join(app.root_path, 'api', 'test', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 确保文件夹存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
# --- JWT 配置 ---
app.config['JWT_SECRET_KEY'] = 'your_very_secret_and_long_key_here' # 生产环境请务必修改
jwt = JWTManager(app)

# --- 数据库连接管理 ---
# 关键: 注册一个函数，在每次请求结束后（无论成功失败）自动关闭数据库连接
app.teardown_appcontext(close_db)

# --- 注册蓝图 ---
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(detection_bp, url_prefix="/api/detection")
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(test_bp, url_prefix='/api/test')

# =============================
# 用于测试的根路径
# =============================
@app.route('/')
def index():
    return jsonify({"message": "Backend running successfully!"}), 200

# =============================
# 初始化数据库管理员账户
# =============================
def init_admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role='admin'")
    admin = cursor.fetchone()

    if not admin:
        print("⚙️ 未检测到管理员账户，正在创建默认管理员：admin / admin123")
        hashed_pw = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ("admin", hashed_pw, "admin")
        )
        conn.commit()
    else:
        print(f"✅ 检测到管理员账户：{admin['username']}")
    
    # 注意：此处不需要手动关闭连接，因为这是在app上下文之外运行的脚本部分
    cursor.close()
    conn.close()

db = SQLAlchemy()
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # 从config.py加载配置 (推荐方式)
    # app.config.from_object('config.Config')
    
    # 或者直接配置
    app.config['SECRET_KEY'] = 'a_very_secret_and_long_key_for_jwt' # <-- 必须和你生成token时用的密钥一样
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # 初始化数据库
    db.init_app(app)
    # === 重要：配置CORS，允许你的前端访问 ===
    # 假设你的Vue前端运行在 http://localhost:5173
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})
    with app.app_context():
        # === 注册你的蓝图 ===
        # 1. 导入我们刚刚创建的蓝图
        from .routes.admin_routes import admin_bp
        # 2. 注册它！
        app.register_blueprint(admin_bp)
        # 3. 注册你已有的其他蓝图 (例如 auth_bp, detection_bp 等)
        # from .routes.auth import auth_bp
        # app.register_blueprint(auth_bp)
        # 创建数据库表
        db.create_all()
    return app
# =============================
# 程序入口
# =============================
if __name__ == '__main__':
    with app.app_context(): # 确保 init_admin 在 app 上下文中运行，以便能找到 g
        init_admin()
    print("🚀 Flask backend starting at http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
