from fastapi import Request
import time
from starlette.datastructures import MutableHeaders
from starlette.types import Message, Receive, Scope, Send

async def logging_middleware(request: Request, call_next):
    print("\n=== Incoming Request ===")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Client: {request.client}")
    print(f"Headers:")
    for name, value in request.headers.items():
        print(f"  {name}: {value}")
    
    # 如果是POST请求，读取并保存请求体
    body = b""
    if request.method == "POST":
        try:
            body = await request.body()
            print(f"Body: {body.decode()}")
            
            # 创建一个新的 receive 函数
            original_receive = request.scope.get('receive', None)
            
            async def receive() -> Message:
                if hasattr(receive, 'body_sent'):
                    return await original_receive()
                receive.body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            
            request.scope['receive'] = receive
            
        except Exception as e:
            print(f"Error reading body: {e}")
    
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        print(f"\n=== Response ===")
        print(f"Status code: {response.status_code}")
        print(f"Process time: {process_time:.4f} seconds")
        print(f"Headers:")
        for name, value in response.headers.items():
            print(f"  {name}: {value}")
        
        # 修改 CORS 头
        headers = MutableHeaders(response.headers)
        headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        headers["Pragma"] = "no-cache"
        headers["Expires"] = "0"
        
        # 创建一个新的响应发送函数
        async def wrapped_send(message: Message) -> None:
            if message['type'] == 'http.response.start':
                message.setdefault('headers', []).extend([
                    (b'access-control-allow-origin', b'http://localhost:5173'),
                    (b'access-control-allow-credentials', b'true'),
                ])
            await response.send(message)
        
        # 替换原始的 send 函数
        response.send = wrapped_send
        
        return response
    except Exception as e:
        print(f"\n=== Error Processing Request ===")
        print(f"Error: {str(e)}")
        raise 