from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

# 注册
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '用户名或密码不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return jsonify({'message': '用户名已存在'}), 400

    hashed_pw = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': '注册成功'}), 200


# 登录
# 登录
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': '用户名或密码错误'}), 401

    # identity 只能放 user_id（字符串）
    # 用户信息放入 "additional_claims"
    token = create_access_token(
        identity=str(user['id']),
        additional_claims={
            "username": user["username"],
            "role": user["role"]
        }
    )

    return jsonify({
        'token': token,
        'role': user['role'],
        'username': user['username']
    }), 200
