# backend/routes/detection.py (完整代码)

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import save_detection

bp = Blueprint('detection', __name__)

@bp.route('/save', methods=['POST'])
@jwt_required()
def save_user_detection():
    data = request.json
    
    # 正确做法：get_jwt_identity() 直接返回用户ID字符串
    user_id = get_jwt_identity()

    if not user_id:
        return jsonify({"msg": "无效的Token，无法获取用户身份"}), 401

    image_path = data.get("image_path")
    label = data.get("label")

    if not image_path or not label:
        return jsonify({"msg": "缺少 'image_path' 或 'label' 参数"}), 400

    # 调用 db.py 中的函数来保存数据
    save_detection(
        user_id=int(user_id),
        image_path=image_path,
        label=label,
        confidence=data.get("confidence")
    )

    return jsonify({"msg": "保存成功"}), 200

# backend/routes/detection.py (新增的代码)

@bp.route('/my-detections', methods=['GET'])
@jwt_required()
def get_my_detections():
    """
    获取当前登录用户提交的所有检测反馈记录。
    """
    # 1. 从 JWT Token 中获取当前用户的 ID
    user_id = get_jwt_identity()

    # 2. 连接数据库
    from db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # 使用 dictionary=True 可以让返回结果是字典形式

    # 3. 编写 SQL 查询语句，根据 user_id 筛选记录
    #    我们选取了所有需要的字段，包括了新的 'upload_status'
    query = """
        SELECT 
            id, 
            image_path, 
            label, 
            confidence, 
            upload_status, 
            created_at 
        FROM detections 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """
    
    # 4. 执行查询
    cursor.execute(query, (user_id,))
    
    # 5. 获取所有查询结果
    user_detections = cursor.fetchall()
    
    cursor.close()
    
    # 6. 将结果以 JSON 格式返回给前端
    return jsonify(user_detections), 200

