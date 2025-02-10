# 库存管理系统

这是一个基于 FastAPI 和 Vue.js 开发的现代化库存管理系统，支持扫码枪集成、商品出入库管理、库存跟踪和报表统计等功能。

## 功能特点

- 商品管理：添加、编辑、删除商品，设置警戒库存
- 入库管理：商品入库，自动计算加权平均成本
- 出库管理：商品出库，支持销售价格记录
- 库存监控：实时库存查看，低库存预警
- 数据统计：支持多维度数据统计和分析
- 扫码集成：支持扫码枪快速录入
- 交易记录：详细的出入库记录查询

## 技术栈

### 后端
- Python 3.8+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

### 前端
- Vue 3
- TypeScript
- Element Plus
- Vue Router
- ECharts

## 安装说明

1. 克隆项目
```bash
git clone [项目地址]
cd kucun_system
```

2. 后端设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库等配置

# 运行迁移脚本
python -m app.db.migrate

# 启动后端服务
uvicorn app.main:app --reload
```

3. 前端设置
```bash
# 安装依赖
cd frontend
npm install

# 配置环境变量
cp .env.example .env

# 启动开发服务器
npm run dev
```

4. 访问系统
- 前端：http://localhost:5173
- 后端API文档：http://localhost:8000/docs

## 开发说明

### 目录结构
```
kucun_system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/
    │   ├── components/
    │   ├── router/
    │   ├── views/
    │   └── App.vue
    └── package.json
```

### 开发规范
- 后端遵循 PEP 8 编码规范
- 前端遵循 Vue 3 组合式 API 规范
- 使用 TypeScript 进行类型检查
- 提交代码前进行代码格式化

## 部署说明

1. 后端部署
- 使用 Gunicorn 作为 WSGI 服务器
- 配置 Nginx 反向代理
- 使用 Supervisor 管理进程

2. 前端部署
- 执行 `npm run build` 构建生产版本
- 将 dist 目录部署到 Web 服务器

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 发起 Pull Request

## 许可证

MIT License 