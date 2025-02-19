# 仓储管理系统

## 项目概述
这是一个基于FastAPI和Vue 3的现代化仓储管理系统，用于管理企业的库存、出入库、财务等业务流程。

### 主要功能
- 库存管理
  - 商品信息管理
  - 库存查询
  - 库存预警
- 入库管理
  - 采购入库
  - 退货入库
  - 入库单管理
- 出库管理
  - 销售出库
  - 退货出库
  - 出库单管理
- 财务管理
  - 收支记录
  - 财务报表
  - 账单管理

## 技术栈

### 后端
- FastAPI - 现代化的Python Web框架
- SQLAlchemy - ORM框架
- Pydantic - 数据验证
- pytest - 单元测试
- Black - 代码格式化
- mypy - 类型检查

### 前端
- Vue 3 - 渐进式JavaScript框架
- TypeScript - 类型安全的JavaScript超集
- Element Plus - UI组件库
- Tailwind CSS - 原子化CSS框架
- Pinia - 状态管理
- Vue Router - 路由管理
- Axios - HTTP客户端
- Jest - 单元测试

## 项目结构

### 后端结构

backend/
├── app/
│   ├── api/          # API路由
│   │   ├── deps.py             # 依赖注入
│   │   └── endpoints/
│   │       ├── inventory.py    # 库存相关API
│   │       ├── stock.py        # 出入库API
│   │       ├── finance.py      # 财务相关API
│   │       ├── auth.py         # 认证相关API
│   │       └── users.py        # 用户管理API
│   ├── core/         # 核心配置
│   │   ├── config.py          # 系统配置
│   │   ├── security.py        # 安全相关
│   │   ├── events.py          # 事件处理
│   │   └── logging.py         # 日志配置
│   ├── crud/         # 数据库操作
│   │   ├── base.py            # 基础CRUD操作
│   │   ├── inventory.py       # 库存CRUD
│   │   ├── finance.py         # 财务CRUD
│   │   ├── stock.py           # 出入库CRUD
│   │   └── user.py            # 用户CRUD
│   ├── db/           # 数据库模型
│   │   ├── base.py            # 基础模型
│   │   ├── models.py          # SQLAlchemy模型
│   │   ├── session.py         # 数据库会话
│   │   └── init_db.py         # 数据库初始化
│   ├── schemas/      # Pydantic模型
│   │   ├── inventory.py       # 库存相关模型
│   │   ├── finance.py         # 财务相关模型
│   │   ├── stock.py           # 出入库相关模型
│   │   ├── user.py            # 用户相关模型
│   │   └── common.py          # 通用模型
│   ├── services/     # 业务逻辑
│   │   ├── inventory.py       # 库存服务
│   │   ├── finance.py         # 财务服务
│   │   ├── stock.py           # 出入库服务
│   │   ├── auth.py            # 认证服务
│   │   └── email.py           # 邮件服务
│   └── utils/        # 工具函数
│       ├── security.py        # 安全工具
│       ├── validators.py      # 验证工具
│       └── helpers.py         # 辅助函数
├── tests/            # 测试文件
│   ├── conftest.py           # 测试配置
│   ├── test_inventory.py     # 库存测试
│   ├── test_finance.py       # 财务测试
│   ├── test_stock.py         # 出入库测试
│   └── test_auth.py          # 认证测试
├── alembic/          # 数据库迁移
│   ├── versions/            # 迁移版本
│   └── env.py              # 迁移环境
├── logs/             # 日志文件
├── requirements.txt  # 依赖包
├── alembic.ini      # Alembic配置
├── .env             # 环境变量
├── .env.example     # 环境变量示例
├── Dockerfile       # Docker配置
└── main.py          # 入口文件

### 前端结构

frontend/
├── src/
│   ├── api/         # API请求
│   │   ├── inventory.ts       # 库存相关API
│   │   ├── finance.ts         # 财务相关API
│   │   ├── stock.ts           # 出入库相关API
│   │   ├── auth.ts            # 认证相关API
│   │   └── user.ts            # 用户相关API
│   ├── assets/      # 静态资源
│   │   ├── images/           # 图片资源
│   │   ├── styles/           # 全局样式
│   │   └── icons/            # 图标资源
│   ├── components/  # 通用组件
│   │   ├── inventory/        # 库存相关组件
│   │   │   ├── ItemList.vue
│   │   │   └── ItemForm.vue
│   │   ├── finance/          # 财务相关组件
│   │   │   ├── TransactionList.vue
│   │   │   └── ReportChart.vue
│   │   ├── stock/            # 出入库相关组件
│   │   │   ├── StockForm.vue
│   │   │   └── StockList.vue
│   │   └── common/           # 通用组件
│   │       ├── BaseTable.vue
│   │       ├── BaseForm.vue
│   │       └── BaseModal.vue
│   ├── composables/ # 组合式函数
│   │   ├── useInventory.ts
│   │   ├── useStock.ts
│   │   ├── useAuth.ts
│   │   └── useTable.ts
│   ├── layouts/     # 布局组件
│   │   ├── MainLayout.vue    # 主布局
│   │   ├── AuthLayout.vue    # 认证布局
│   │   └── components/       # 布局组件
│   │       ├── Sidebar.vue
│   │       ├── Header.vue
│   │       └── Footer.vue
│   ├── router/      # 路由配置
│   │   ├── index.ts          # 路由入口
│   │   ├── routes.ts         # 路由定义
│   │   └── guards.ts         # 路由守卫
│   ├── stores/      # Pinia状态
│   │   ├── inventory.ts      # 库存状态
│   │   ├── finance.ts        # 财务状态
│   │   ├── stock.ts          # 出入库状态
│   │   ├── user.ts           # 用户状态
│   │   └── app.ts            # 应用状态
│   ├── types/       # TypeScript类型
│   │   ├── inventory.ts      # 库存类型
│   │   ├── finance.ts        # 财务类型
│   │   ├── stock.ts          # 出入库类型
│   │   ├── user.ts           # 用户类型
│   │   └── common.ts         # 通用类型
│   ├── utils/       # 工具函数
│   │   ├── request.ts        # axios封装
│   │   ├── auth.ts           # 认证工具
│   │   ├── validator.ts      # 验证工具
│   │   └── helpers.ts        # 辅助函数
│   └── views/       # 页面组件
│       ├── inventory/        # 库存页面
│       │   ├── List.vue
│       │   └── Detail.vue
│       ├── stock/            # 出入库页面
│       │   ├── StockIn.vue
│       │   └── StockOut.vue
│       ├── finance/          # 财务页面
│       │   ├── Finance.vue
│       │   └── Report.vue
│       └── auth/             # 认证页面
│           ├── Login.vue
│           └── Register.vue
├── tests/           # 测试文件
│   ├── unit/               # 单元测试
│   │   ├── components/
│   │   └── stores/
│   └── e2e/                # E2E测试
├── public/          # 静态资源
│   ├── favicon.ico
│   └── images/
├── index.html       # 入口HTML
├── package.json     # 项目配置
├── tsconfig.json    # TypeScript配置
├── vite.config.ts   # Vite配置
├── tailwind.config.js # Tailwind配置
├── .eslintrc.js    # ESLint配置
├── .prettierrc     # Prettier配置
├── Dockerfile      # Docker配置
└── nginx.conf      # Nginx配置

## 核心功能模块

### 1. 库存管理模块
- 商品基础信息维护
- 库存实时查询
- 库存预警设置
- 库存变动记录
- 库存盘点功能

### 2. 入库管理模块 (StockIn.vue)
- 采购入库单创建
- 入库单审核流程
- 供应商管理
- 入库记录查询
- 入库单打印

### 3. 出库管理模块 (StockOut.vue)
- 销售出库单创建
- 出库单审核流程
- 客户管理
- 出库记录查询
- 出库单打印

### 4. 财务管理模块 (Finance.vue)
- 收支记录管理
- 财务报表生成
- 应收应付管理
- 成本核算
- 财务分析

## API接口说明

### 库存相关接口
# backend/app/api/endpoints/inventory.py

GET /api/inventory/items          # 获取库存列表
POST /api/inventory/items         # 新增库存项
GET /api/inventory/items/{id}     # 获取单个库存详情
PUT /api/inventory/items/{id}     # 更新库存信息
DELETE /api/inventory/items/{id}  # 删除库存项

### 出入库相关接口
# backend/app/api/endpoints/inventory.py

POST /api/inventory/stock-in      # 创建入库单
POST /api/inventory/stock-out     # 创建出库单
GET /api/inventory/records        # 获取出入库记录
PUT /api/inventory/approve/{id}   # 审核出入库单

## 开发规范

### 后端开发规范
1. 使用Black进行代码格式化
2. 所有函数必须包含类型注解
3. 使用Pydantic进行数据验证
4. 编写单元测试，确保覆盖率
5. 遵循RESTful API设计规范

### 前端开发规范
1. 使用TypeScript编写所有组件
2. 使用Composition API风格
3. 使用Element Plus组件库
4. 使用Tailwind CSS进行样式开发
5. 保持组件的单一职责

## 部署说明

### 开发环境
# 后端启动
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端启动
cd frontend
npm install
npm run dev

### 生产环境
# 使用Docker Compose
docker-compose up -d

## 安全措施
1. JWT身份认证
2. RBAC权限控制
3. 请求速率限制
4. 数据加密存储
5. SQL注入防护
6. XSS攻击防护

## 性能优化
1. Redis缓存热点数据
2. 数据库索引优化
3. 大数据量分页处理
4. 前端组件懒加载
5. 静态资源CDN加速

## 更新日志

### v1.0.0 (2024-01)
- 实现基础的库存管理功能
- 完成出入库流程
- 集成基础财务功能

## 维护者
- 技术团队

## 许可证
MIT License
