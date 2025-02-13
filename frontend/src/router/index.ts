import { createRouter, createWebHistory } from 'vue-router';
import Layout from '../components/Layout.vue';

const routes = [
    {
        path: '/',
        component: Layout,
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('../views/Dashboard.vue'),
                meta: { title: '仪表盘' }
            },
            {
                path: 'inventory',
                name: 'Inventory',
                component: () => import('../views/Inventory.vue'),
                meta: { title: '库存管理' }
            },
            {
                path: 'stock-in',
                name: 'StockIn',
                component: () => import('../views/StockIn.vue'),
                meta: { title: '商品入库' }
            },
            {
                path: 'stock-out',
                name: 'StockOut',
                component: () => import('../views/StockOut.vue'),
                meta: { title: '商品出库' }
            },
            {
                path: 'transactions',
                name: 'Transactions',
                component: () => import('../views/Transactions.vue'),
                meta: { title: '交易记录' }
            },
            {
                path: 'performance',
                name: 'Performance',
                component: () => import('../views/Performance.vue'),
                meta: { title: '业绩统计' }
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

export default router; 