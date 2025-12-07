# backend/routes/admin.py (完整代码)
import os
from flask import Blueprint, request, jsonify,current_app 
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps
from db import get_db_connection
import requests

# 创建 admin 蓝图
admin_bp = Blueprint("admin", __name__)


# --- 1. 自定义管理员权限验证装饰器 ---
# 这是一个非常好的实践，让代码更清晰、更安全
def admin_required(fn):
    @wraps(fn)
    @jwt_required()  # 首先确保用户已登录
    def wrapper(*args, **kwargs):
        # 使用 get_jwt() 获取完整的 Token 负载 (payload)
        claims = get_jwt()
        # 检查 'role' 声明是否存在且值为 'admin'
        if claims.get("role") != "admin":
            return jsonify({"msg": "管理员权限不足"}), 403
        # 如果权限验证通过，则执行原始的路由函数
        return fn(*args, **kwargs)
    return wrapper


# --- 2. 获取所有检测记录 (支持过滤) ---
# GET /api/admin/detections?filter=all|processed|unprocessed
@admin_bp.route("/detections", methods=["GET"])
@admin_required  # <-- 使用我们自定义的装饰器
def get_detections():
    filter_status = request.args.get("filter", "all", type=str).lower()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 基础查询语句，包含用户名字段
    base_query = """
        SELECT 
            d.id, d.image_path, d.label, d.confidence, 
            d.is_processed, d.admin_uploaded, d.upload_status, 
            d.create_at, u.username 
        FROM detections d
        JOIN users u ON d.user_id = u.id
    """

    if filter_status == "processed":
        cursor.execute(f"{base_query} WHERE d.is_processed = 1 ORDER BY d.id DESC")
    elif filter_status == "unprocessed":
        cursor.execute(f"{base_query} WHERE d.is_processed = 0 ORDER BY d.id DESC")
    else:  # 'all'
        cursor.execute(f"{base_query} ORDER BY d.id DESC")
        
    data = cursor.fetchall()
    # 不需要手动关闭连接
    return jsonify(data), 200


# --- 3. 标记单条检测记录为"已处理" ---
# POST /api/admin/mark_processed/<id>
@admin_bp.route("/mark_processed/<int:detect_id>", methods=["POST"])
@admin_required
def mark_processed(detect_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE detections SET is_processed = 1 WHERE id = %s",
        (detect_id,)
    )
    # 检查是否有记录被更新
    if cursor.rowcount == 0:
        return jsonify({"msg": f"未找到ID为 {detect_id} 的记录"}), 404
        
    conn.commit()
    return jsonify({"msg": "已成功标记为已处理"}), 200


# --- 4. 管理员进行“上传 / 不上传”选择 (保留接口) ---
# POST /api/admin/upload_choice/<id>
@admin_bp.route("/upload_choice/<int:detect_id>", methods=["POST"])
@admin_required
def upload_choice(detect_id):
    data = request.get_json()
    choice = data.get("choice")

    if choice not in ["upload", "skip"]:
        return jsonify({"msg": "无效的 'choice' 参数，必须是 'upload' 或 'skip'"}), 400

    admin_uploaded_flag = 1 if choice == "upload" else 0
    upload_status_msg = "uploaded_by_admin" if choice == "upload" else "skipped_by_admin"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE detections SET admin_uploaded = %s, upload_status = %s WHERE id = %s",
        (admin_uploaded_flag, upload_status_msg, detect_id)
    )
    if cursor.rowcount == 0:
        return jsonify({"msg": f"未找到ID为 {detect_id} 的记录"}), 404
        
    conn.commit()
    return jsonify({"msg": "操作成功", "status": upload_status_msg}), 200


import requests  # 1. 导入 requests 库
import os
from flask import current_app, jsonify, request
# ... 其他导入

# 2. 定义你的 AI 模型后台的地址
#    如果它们运行在同一台机器但不同端口，就是类似 'http://localhost:5001/feedback'
#    请根据你的实际部署情况修改
AI_SERVICE_URL = 'http://127.0.0.1:8000/feedback' 

@admin_bp.route('/process_detection', methods=['POST'])
def process_detection():
    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({'error': '请求体中缺少 "ids" 字段'}), 400

    detection_ids = data['ids']
    if not isinstance(detection_ids, list):
        return jsonify({'error': '"ids" 必须是一个列表'}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        return jsonify({'error': '服务器内部配置错误: UPLOAD_FOLDER 未定义'}), 500

    success_count = 0
    failures = []

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    for detection_id in detection_ids:
        try:
            # 3. 修改 SQL 查询，同时获取图片路径和正确的标签
            cursor.execute("SELECT image_path, label FROM detections WHERE id = %s", (detection_id,))
            record = cursor.fetchone()

            if not record:
                failures.append({'id': detection_id, 'reason': '记录未找到'})
                continue

            image_url_path = record['image_path']
            # 4. 从记录中获取 correct_label
            correct_label = record['label'] 

            filename = os.path.basename(image_url_path)
            physical_file_path = os.path.join(upload_folder, filename)

            if not os.path.exists(physical_file_path):
                failures.append({'id': detection_id, 'reason': f'文件不存在: {filename}'})
                continue
            
            # --- 新增的调用逻辑 ---
            # 5. 打开图片文件，并准备发送
            with open(physical_file_path, 'rb') as f:
                files = {'file': (filename, f, 'image/jpeg')} # 假设是 jpeg，也可以是其他类型
                payload = {'correct_label': correct_label}
                
                # 6. 发送 POST 请求到 AI 模型后台
                response = requests.post(AI_SERVICE_URL, files=files, data=payload)

                # 7. 检查 AI 模型后台的响应
                if response.status_code == 200:
                    # 只有当 AI 后台成功接收后，我们才更新数据库状态
                    cursor.execute("""
                        UPDATE detections
                        SET is_processed = TRUE,
                            upload_status = %s
                        WHERE id = %s
                    """, ('uploaded', detection_id))
                    conn.commit()
                    current_app.logger.info(f"成功处理并发送记录 ID {detection_id} 到 AI 服务")
                    success_count += 1
                else:
                    # 如果 AI 后台返回错误，记录失败
                    conn.rollback() # 回滚事务
                    reason = f"AI 服务返回错误: {response.status_code} - {response.text}"
                    failures.append({'id': detection_id, 'reason': reason})
                    current_app.logger.error(f"发送记录 ID {detection_id} 到 AI 服务失败: {reason}")
            # --- 新增逻辑结束 ---

        except Exception as e:
            conn.rollback()
            failures.append({'id': detection_id, 'reason': str(e)})
            current_app.logger.error(f"处理记录 ID {detection_id} 失败: {e}", exc_info=True)

    cursor.close()
    conn.close()

    return jsonify({
        'message': '处理完成',
        'success_count': success_count,
        'failure_count': len(failures),
        'failures': failures
    }), 200