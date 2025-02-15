# 库存管理系统项目结构说明

## 核心文件

### backend/app/main.py
主应用入口文件，负责:
- 创建 FastAPI 应用实例
- 配置中间件(CORS、日志等)
- 注册路由
- 配置启动和关闭事件
- 提供基础测试路由

### backend/app/core/
核心配置目录:

#### config.py
系统配置文件，包含:
- 数据库连接配置
- JWT 认证配置
- 扫码枪配置
- 其他系统参数

#### auth.py
认证相关功能:
- JWT token 的创建和验证
- 用户认证中间件
- 权限验证

## API 端点 (backend/app/api/endpoints/)

### auth.py
认证相关接口:
- 用户登录
- Token 验证

### inventory.py
库存管理相关接口:
- 商品 CRUD
- 入库/出库操作
- 库存统计
- 商品分析
- 业绩统计

### log.py
日志相关接口:
- 操作日志查询
- 日志记录

### user.py
用户管理相关接口:
- 用户 CRUD
- 权限管理
- 用户认证

## 数据库相关 (backend/app/db/)

### session.py
数据库会话管理:
- 创建数据库引擎
- 配置连接池
- 提供数据库会话

### migrate.py
数据库迁移工具:
- 数据库结构更新
- 字段变更
- 数据迁移

## 中间件 (backend/app/middleware/)

### logging.py
日志中间件:
- 请求日志记录
- 响应日志记录
- CORS 头部处理

## 数据模型 (backend/app/models/)

### inventory.py
库存相关模型:
- Inventory (商品)
- Transaction (交易记录)

### log.py
日志模型:
- OperationLog (操作日志)

### user.py
用户相关模型:
- User (用户)
- Store (商店)

## 数据模式 (backend/app/schemas/)

### inventory.py
库存相关数据模式:
- 商品创建/更新
- 交易记录
- 统计数据
- 分析数据

### log.py
日志相关数据模式:
- 操作日志响应

### user.py
用户相关数据模式:
- 用户创建/更新
- 商店创建
- Token 数据

## 服务层 (backend/app/services/)

### inventory.py
库存服务:
- 商品管理
- 库存操作
- 统计分析
- 交易处理

### user.py
用户服务:
- 用户管理
- 认证服务
- 权限控制

## 工具类 (backend/app/utils/)

### scanner.py
扫码枪工具:
- 串口通信
- 条码读取
- 异步处理

## 特点

1. 分层架构:
   - API 层 (endpoints)
   - 服务层 (services)
   - 数据层 (models)
   - 工具层 (utils)

2. 完善的错误处理:
   - 异常捕获
   - 事务管理
   - 日志记录

3. 安全特性:
   - JWT 认证
   - 权限控制
   - 数据验证

4. 性能优化:
   - 数据库连接池
   - 异步处理
   - 缓存机制

5. 可扩展性:
   - 模块化设计
   - 清晰的依赖关系
   - 统一的接口规范

这个项目采用了现代化的后端架构设计，具有良好的可维护性和扩展性。通过分层设计和模块化组织，使得代码结构清晰，便于理解和维护。 