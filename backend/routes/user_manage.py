import functools
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from db import get_db_connection

# 创建一个新的蓝图，专门用于管理员的用户管理
# 注意：我们将这个蓝图命名为 user_admin_bp 以避免与你现有的 admin_bp 冲突
user_admin_bp = Blueprint('user_admin', __name__)

# --- 装饰器：检查管理员权限 ---
def admin_required(fn):
    """
    一个装饰器，用于保护路由，只允许角色为 'admin' 的用户访问。
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # 从JWT中获取当前用户的声明信息
        claims = get_jwt()
        # 检查 'role' 是否为 'admin'
        if claims.get("role") != "admin":
            return jsonify({"message": "管理员权限不足"}), 403 # 403 Forbidden
        # 如果是管理员，则正常执行路由函数
        return fn(*args, **kwargs)
    return wrapper


# --- API 路由 ---

# 1. 获取所有用户列表
@user_admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """
    [GET] /api/admin/users
    获取系统内所有用户的信息。
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # 查询时排除密码字段，增加安全性
        cursor.execute("SELECT id, username, role, create_at FROM users ORDER BY id ASC")
        users = cursor.fetchall()
        cursor.close()
        # 注意：不需要手动关闭 conn，app.teardown_appcontext 会处理
        return jsonify(users), 200
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({"message": "获取用户列表失败"}), 500

# 2. 手动添加用户
@user_admin_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required
def add_user():
    """
    [POST] /api/admin/users
    管理员手动添加一个新用户（可以是普通用户或管理员）。
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # 如果前端没提供role，默认为'user'

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    if role not in ['user', 'admin']:
        return jsonify({'message': '无效的角色'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'message': '用户名已存在'}), 409 # 409 Conflict

        hashed_pw = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed_pw, role)
        )
        conn.commit()
        
        # 获取刚刚插入的用户ID，以便返回完整用户信息
        new_user_id = cursor.lastrowid
        cursor.execute("SELECT id, username, role, create_at FROM users WHERE id=%s", (new_user_id,))
        new_user = cursor.fetchone()
        
        cursor.close()
        return jsonify(new_user), 201 # 201 Create
    except Exception as e:
        print(f"Error adding user: {e}")
        return jsonify({"message": "添加用户失败"}), 500


# 3. 重置用户密码
@user_admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
@admin_required
def reset_password(user_id):
    """
    [POST] /api/admin/users/<user_id>/reset-password
    重置指定用户的密码为一个默认值。
    """
    # 为安全起见，不允许管理员重置自己的密码
    # claims = get_jwt()
    # if str(user_id) == claims.get('sub'): # 'sub' is the user_id
    #     return jsonify({"message": "不能通过此接口重置自己的密码"}), 400

    try:
        # 定义一个简单易记的默认新密码
        new_password_plain = "newpassword123"
        hashed_new_password = generate_password_hash(new_password_plain)

        conn = get_db_connection()
        cursor = conn.cursor()

        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"message": "用户不存在"}), 404

        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hashed_new_password, user_id)
        )
        conn.commit()
        cursor.close()

        # 返回新的明文密码，方便管理员告知用户
        return jsonify({
            "message": f"用户ID {user_id} 的密码已重置",
            "new_password": new_password_plain
        }), 200
    except Exception as e:
        print(f"Error resetting password for user {user_id}: {e}")
        return jsonify({"message": "重置密码失败"}), 500

@user_admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """
    [DELETE] /api/admin/users/<user_id>
    删除指定用户，以及其在 detections 表中的所有记录。
    """
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 防止管理员删自己
        current_user_id = get_jwt_identity()
        if int(user_id) == int(current_user_id):
            return jsonify({"message": "不能删除自己"}), 400

        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"message": "用户不存在"}), 404

        # ---- 开始事务（不需要 start_transaction）----
        conn.autocommit = False

        # 删除 detections
        cursor.execute("DELETE FROM detections WHERE user_id=%s", (user_id,))

        # 删除用户
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

        # 提交事务
        conn.commit()

        return jsonify({"message": f"用户 {user_id} 已成功删除"}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error deleting user {user_id}: {e}")
        return jsonify({"message": "删除用户失败", "error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
