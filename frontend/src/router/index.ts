import { createRouter, createWebHistory } from 'vue-router';
import Layout from '../components/Layout.vue';
import ProductAnalysis from '../views/ProductAnalysis.vue';

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
                meta: { title: '仪表盘', icon: 'Odometer' }
            },
            {
                path: 'inventory',
                name: 'Inventory',
                component: () => import('../views/Inventory.vue'),
                meta: { title: '库存管理', icon: 'List' }
            },
            {
                path: 'stock-in',
                name: 'StockIn',
                component: () => import('../views/StockIn.vue'),
                meta: { title: '商品入库', icon: 'Plus' }
            },
            {
                path: 'stock-out',
                name: 'StockOut',
                component: () => import('../views/StockOut.vue'),
                meta: { title: '商品出库', icon: 'Minus' }
            },
            {
                path: 'transactions',
                name: 'Transactions',
                component: () => import('../views/Transactions.vue'),
                meta: { title: '交易记录', icon: 'Tickets' }
            },
            {
                path: 'performance',
                name: 'Performance',
                component: () => import('../views/Performance.vue'),
                meta: { title: '业绩统计', icon: 'DataLine' }
            },
            {
                path: 'analysis',
                name: 'ProductAnalysis',
                component: ProductAnalysis,
                meta: { title: '商品分析', icon: 'TrendCharts' }
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