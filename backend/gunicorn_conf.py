# 工作进程数
workers = 4
# 每个工作进程的线程数
threads = 2
# 绑定的IP和端口
bind = '127.0.0.1:8000'
# 守护进程模式
daemon = True
# 访问日志和错误日志
accesslog = '/var/log/kucun/access.log'
errorlog = '/var/log/kucun/error.log'
# 进程名称
proc_name = 'kucun_api'
# 工作模式
worker_class = 'uvicorn.workers.UvicornWorker' 