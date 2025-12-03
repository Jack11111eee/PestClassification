模型纠错反馈 API
1. 功能描述:
当用户认为预测结果不正确时，将原始图片和正确的病害名称一起提交，用于后续的模型优化。

2. 接口地址 (Endpoint):

URL:http://127.0.0.1:8000/feedback
请求方法: POST
3. 请求格式 (Request):

Headers: Content-Type: multipart/form-data
Body: 请求体必须包含两个字段：
字段1 (文件):
Key: file
Value: 用户上传的原始图片文件。
字段2 (表单数据):
Key: correct_label
Value: 用户选择的正确病害名称（字符串）。