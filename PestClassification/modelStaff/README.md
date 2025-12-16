病虫害识别 API 文档
1. 功能描述:
上传一张植物叶片图片，接口会返回最可能的病虫害类别及其置信度。

2. 接口地址 (Endpoint):
URL:http://127.0.0.1:8000/predict
请求方法: POST

3. 请求格式 (Request):

Headers: Content-Type: multipart/form-data
Body: 请求体中必须包含一个文件字段。
字段名 (Key): file
字段值 (Value): 图片的二进制文件内容。
4. 成功响应 (Success Response):

状态码: 200 OK
内容 (JSON Body):
<JSON>
{
  "prediction": {
    "class_name": "Tomato___Late_blight",
    "confidence": 0.9987
  },
  "model_info": {
    "total_classes": 42
  }
}
5. 失败响应 (Error Response):

未上传文件:
状态码: 400 Bad Request
内容: {"error": "请求中未找到文件部分(file part not found in request)"}
服务器内部错误:
状态码: 500 Internal Server Error
内容: {"error": "预测失败: [具体错误信息]"}