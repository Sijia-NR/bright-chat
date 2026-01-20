# Bright-Chat Mock Server

## 简介

这是Bright-Chat项目的大模型智能应用服务模拟服务，基于FastAPI实现。用于开发和测试阶段模拟真实的AI模型接口。

## 功能特性

- ✅ 语义大模型服务接口（chat/completions）
- ✅ 视觉大模型服务接口（lvm/completions）
- ✅ 多模态大模型服务接口（vlm/chat/completions）
- ✅ 支持流式和非流式响应
- ✅ 完整的请求验证和错误处理
- ✅ 鉴权验证
- ✅ CORS支持

## 接口规范

基于《大模型智能应用服务接口规范.txt》实现，支持以下接口：

### 1. 语义大模型服务
- **接口地址**: `/lmp-cloud-ias-server/api/llm/chat/completions`
- **接口地址V2**: `/lmp-cloud-ias-server/api/llm/chat/completions/V2`
- **请求方式**: POST
- **支持参数**: model, messages, stream, temperature, top_p, presence_penalty, tools, tool_choice等

### 2. 视觉大模型服务
- **接口地址**: `/lmp-cloud-ias-server/api/lvm/completions`
- **请求方式**: POST
- **支持参数**: data, model, modelVersion等

### 3. 多模态大模型服务
- **接口地址**: `/lmp-cloud-ias-server/api/vlm/chat/completions`
- **接口地址V2**: `/lmp-cloud-ias-server/api/vlm/chat/completions/V2`
- **请求方式**: POST
- **支持参数**: model, messages, stream, temperature, top_p, presence_penalty等

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python start.py
```

或者使用uvicorn直接启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 18063 --reload
```

### 3. 访问服务

服务启动后，可以通过以下地址访问：

- **API文档**: http://localhost:18063/docs
- **ReDoc文档**: http://localhost:18063/redoc
- **根路径**: http://localhost:18063/

## 使用示例

### 语义大模型调用

```bash
curl -X POST "http://localhost:18063/lmp-cloud-ias-server/api/llm/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: APP_KEY" \
  -d '{
    "model": "BrightChat-General-v1",
    "messages": [
      {
        "role": "user",
        "content": "你好，介绍下南京"
      }
    ],
    "stream": false
  }'
```

### 视觉大模型调用

```bash
curl -X POST "http://localhost:18063/lmp-cloud-ias-server/api/lvm/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: APP_KEY" \
  -d '{
    "model": "vision-model",
    "data": [
      {
        "image_name": "test.jpg",
        "image_type": "url",
        "image_data": "http://example.com/test.jpg"
      }
    ]
  }'
```

### 多模态大模型调用

```bash
curl -X POST "http://localhost:18063/lmp-cloud-ias-server/api/vlm/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: APP_KEY" \
  -d '{
    "model": "SGGM-VL-7B",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "图片是什么？"
          }
        ]
      }
    ],
    "stream": false
  }'
```

## 配置说明

主要配置项在 `config.py` 中：

- `PORT`: 服务端口，默认18063
- `APP_ID`: 应用ID
- `DEFAULT_APP_KEY`: 默认鉴密钥
- `RESPONSE_DELAY_MIN/MAX`: 响应延迟范围
- `SUPPORTED_MODELS`: 支持的模型列表

## 环境变量

可以通过环境变量配置：

```bash
export MOCK_SERVER_PORT=18063
```

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 000000 | 成功 |
| 100000 | 失败 |
| 200001 | 请求参数不是标准的JSON格式 |
| 200002 | 请求参数错误 |
| 200003 | 必填字段为空 |
| 200004 | 参数长度超过限制 |
| 200005 | 参数枚举值无效 |
| 300001 | 鉴权失败 |
| 300002 | 权限被拒绝 |
| 400001 | 服务器内部错误 |
| 400002 | 远程服务调用失败 |

## 注意事项

1. 所有接口都需要在请求头中携带 `Authorization` 字段
2. 流式响应使用 `text/event-stream` 格式
3. 模拟数据会随机生成，确保接口可用性
4. 支持CORS，可以直接在前端调用