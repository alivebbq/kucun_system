from fastapi import Request
import time
from starlette.datastructures import MutableHeaders
from starlette.types import Message, Receive, Scope, Send

async def logging_middleware(request: Request, call_next):
    # 1. 记录请求信息
    print("\n=== Incoming Request ===")
    print(f"Method: {request.method}")  # 记录HTTP方法(GET/POST等)
    print(f"URL: {request.url}")        # 记录请求URL
    print(f"Client: {request.client}")   # 记录客户端信息
    print(f"Headers:")                   # 记录请求头
    for name, value in request.headers.items():
        print(f"  {name}: {value}")
    
    # 2. 处理POST请求的body
    body = b""
    if request.method == "POST":
        try:
            body = await request.body()
            print(f"Body: {body.decode()}")  # 记录POST请求体
            
            # 重新构造receive函数，确保body可以被多次读取
            original_receive = request.scope.get('receive', None)
            async def receive() -> Message:
                if hasattr(receive, 'body_sent'):
                    return await original_receive()
                receive.body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            request.scope['receive'] = receive
            
        except Exception as e:
            print(f"Error reading body: {e}")
    
    # 3. 性能监控
    start_time = time.time()
    try:
        # 4. 处理请求并记录响应信息
        response = await call_next(request)
        process_time = time.time() - start_time
        
        print(f"\n=== Response ===")
        print(f"Status code: {response.status_code}")  # 记录响应状态码
        print(f"Process time: {process_time:.4f} seconds")  # 记录处理时间
        print(f"Headers:")
        for name, value in response.headers.items():
            print(f"  {name}: {value}")
        
        # 5. CORS头处理
        headers = MutableHeaders(response.headers)
        headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        headers["Pragma"] = "no-cache"
        headers["Expires"] = "0"
        
        # 6. 包装响应发送函数
        async def wrapped_send(message: Message) -> None:
            if message['type'] == 'http.response.start':
                message.setdefault('headers', []).extend([
                    (b'access-control-allow-origin', b'http://localhost:5173'),
                    (b'access-control-allow-credentials', b'true'),
                ])
            await response.send(message)
        
        response.send = wrapped_send
        
        return response
        
    except Exception as e:
        # 7. 错误处理和日志记录
        print(f"\n=== Error Processing Request ===")
        print(f"Error: {str(e)}")
        raise 