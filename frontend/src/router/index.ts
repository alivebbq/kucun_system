import { createRouter, createWebHistory } from 'vue-router';
import { useUserStore } from '../stores/user';
import Layout from '../components/Layout.vue';

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        component: Layout,
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('../views/Dashboard.vue'),
                meta: {
                    title: '仪表盘',
                    icon: 'Odometer',
                    requiresAuth: true
                }
            },
            {
                path: 'inventory',
                name: 'Inventory',
                component: () => import('../views/Inventory.vue'),
                meta: {
                    title: '库存管理',
                    icon: 'List',
                    requiresAuth: true,
                    permission: 'inventory'
                }
            },
            {
                path: 'stock-in',
                name: 'StockIn',
                component: () => import('../views/StockIn.vue'),
                meta: {
                    title: '商品入库',
                    icon: 'Plus',
                    requiresAuth: true,
                    permission: 'stock_in'
                }
            },
            {
                path: 'stock-out',
                name: 'StockOut',
                component: () => import('../views/StockOut.vue'),
                meta: {
                    title: '商品出库',
                    icon: 'Minus',
                    requiresAuth: true,
                    permission: 'stock_out'
                }
            },
            {
                path: 'transactions',
                name: 'Transactions',
                component: () => import('../views/Transactions.vue'),
                meta: {
                    title: '交易记录',
                    icon: 'Tickets',
                    requiresAuth: true,
                    permission: 'transactions'
                }
            },
            {
                path: 'performance',
                name: 'Performance',
                component: () => import('../views/Performance.vue'),
                meta: {
                    title: '业绩统计',
                    icon: 'DataLine',
                    requiresAuth: true,
                    permission: 'performance'
                }
            },
            {
                path: 'analysis',
                name: 'ProductAnalysis',
                component: () => import('../views/ProductAnalysis.vue'),
                meta: {
                    title: '商品分析',
                    icon: 'TrendCharts',
                    requiresAuth: true,
                    permission: 'analysis'
                }
            },
            {
                path: 'users',
                name: 'Users',
                component: () => import('../views/Users.vue'),
                meta: {
                    title: '员工管理',
                    icon: 'User',
                    requiresAuth: true,
                    requiresOwner: true
                }
            }
        ]
    },
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// 路由守卫
router.beforeEach((to, from, next) => {
    const userStore = useUserStore();

    // 设置页面标题
    const baseTitle = '库存管理系统';
    document.title = to.meta.title
        ? `${to.meta.title} - ${baseTitle}`
        : baseTitle;

    // 检查路由是否需要认证
    if (to.meta.requiresAuth && !userStore.isLoggedIn) {
        next('/login');
        return;
    }

    // 检查是否需要店主权限
    if (to.meta.requiresOwner && !userStore.isOwner) {
        next('/');
        return;
    }

    // 检查是否有对应权限
    if (to.meta.permission && !userStore.hasPermission(to.meta.permission as string)) {
        next('/');
        return;
    }

    // 如果已登录且访问登录页，重定向到首页
    if (to.path === '/login' && userStore.isLoggedIn) {
        next('/');
        return;
    }

    next();
});

export default router; 