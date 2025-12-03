# routes/admin_routes.py

from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash
from functools import wraps
import jwt

# 假设你的 User 模型和 db 实例在 models.py 文件中定义
from ..models import User, db 
# 假设你的 Flask app 实例和它的配置在主文件中
from .. import app 

# 创建一个名为 'admin_bp' 的蓝图
# url_prefix='/api/admin' 会自动为这个蓝图下的所有路由添加 /api/admin 前缀
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/api/admin')

# =================================================================
# 1. 管理员权限验证装饰器 (非常重要!)
#    这个装饰器会保护所有需要管理员权限的接口
# =================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        # 从请求头中获取 'Authorization'
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            # 标准的 'Bearer [token]' 格式
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'msg': '缺少Token'}), 401

        try:
            # 使用你的密钥解码JWT
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # 检查角色是否为 'admin'
            if payload.get('role') != 'admin':
                return jsonify({'msg': '权限不足，需要管理员权限'}), 403
            
            # 将当前管理员ID存入g对象，方便后续使用 (例如防止删除自己)
            g.current_admin_id = payload.get('sub')

        except jwt.ExpiredSignatureError:
            return jsonify({'msg': 'Token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'msg': 'Token无效'}), 401

        return f(*args, **kwargs)
    return decorated_function


# =================================================================
# 2. 实现我们之前设计的四个API端点
# =================================================================

# 接口一: GET /api/admin/users - 获取所有用户列表
@admin_bp.route('/users', methods=['GET'])
@admin_misc
def get_users():
    """获取所有用户的列表, 不包含密码哈希。"""
    try:
        users = User.query.all()
        # 构建一个不含密码的字典列表返回给前端
        users_list = [
            {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT') # 保持格式一致
            } 
            for user in users
        ]
        return jsonify(users_list), 200
    except Exception as e:
        return jsonify({'msg': f'获取用户列表失败: {str(e)}'}), 500


# 接口二: POST /api/admin/users - 创建新用户
@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """管理员手动创建新用户或管理员。"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user') # 默认为'user'

    if not username or not password:
        return jsonify({'msg': '用户名和密码不能为空'}), 400
    
    if role not in ['user', 'admin']:
        return jsonify({'msg': '无效的角色'}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({'msg': '用户名已存在'}), 409 # 409 Conflict

    # 对密码进行哈希加密
    hashed_password = generate_password_hash(password)
    
    new_user = User(username=username, password_hash=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'msg': '用户创建成功'}), 201 # 201 Created


# 接口三: PUT /api/admin/users/<int:user_id>/reset-password - 重置密码
@admin_bp.route('/users/<int:user_id>/reset-password', methods=['PUT'])
@admin_required
def reset_user_password(user_id):
    """重置指定用户的密码。"""
    data = request.get_json()
    new_password = data.get('password')

    if not new_password:
        return jsonify({'msg': '新密码不能为空'}), 400

    user_to_reset = User.query.get(user_id)
    if not user_to_reset:
        return jsonify({'msg': '用户不存在'}), 404 # 404 Not Found

    # 更新密码哈希
    user_to_reset.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({'msg': f'用户 {user_to_reset.username} 的密码重置成功'}), 200


# 接口四: DELETE /api/admin/users/<int:user_id> - 删除用户
@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除指定用户。"""
    # 关键安全检查：防止管理员删除自己
    if g.current_admin_id == user_id:
        return jsonify({'msg': '不能删除自己'}), 403 # 403 Forbidden

    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        return jsonify({'msg': '用户不存在'}), 404

    db.session.delete(user_to_delete)
    db.session.commit()
    
    return jsonify({'msg': '用户删除成功'}), 200

