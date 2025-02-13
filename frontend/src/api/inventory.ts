import api from './config';

export interface Inventory {
    id: number;
    barcode: string;
    name: string;
    unit: string;
    avg_purchase_price: number;
    selling_price: number;
    avg_selling_price: number;
    stock: number;
    warning_stock: number;
    created_at: string;
    updated_at: string;
}

export interface Transaction {
    id: number;
    barcode: string;
    type: 'in' | 'out';
    quantity: number;
    price: number;
    total: number;
    timestamp: string;
}

// 库存预警商品
export interface LowStockItem {
    barcode: string;
    name: string;
    stock: number;
    warning_stock: number;
    unit: string;
}

// 库存统计响应
export interface InventoryStats {
    total_value: number;
    today_sales: number;
    week_sales: number;
    low_stock_items: LowStockItem[];
    hot_products: HotProduct[];
}

export interface TransactionResponse {
    items: Transaction[];
    total: number;
}

// 获取库存列表
export const getInventoryList = (params?: { skip?: number; limit?: number }) => {
    return api.get<Inventory[]>('/inventory/', { params });
};

// 根据条形码获取商品
export const getInventoryByBarcode = (barcode: string) => {
    return api.get<Inventory>(`/inventory/${barcode}`);
};

// 创建商品
export const createInventory = (data: Partial<Inventory>) => {
    return api.post<Inventory>('/inventory/', data);
};

// 更新商品
export const updateInventory = (barcode: string, data: Partial<Inventory>) => {
    return api.put<Inventory>(`/inventory/${barcode}`, data);
};

// 商品入库
export const stockIn = (data: { barcode: string; quantity: number; price: number }) => {
    return api.post<Inventory>('/inventory/stock-in', data);
};

// 商品出库
export const stockOut = (data: { barcode: string; quantity: number; price: number }) => {
    return api.post<Inventory>('/inventory/stock-out', data);
};

// 获取库存统计
export const getInventoryStats = () => {
    return api.get<InventoryStats>('/stats');
};

// 获取交易记录
export const getTransactions = (params?: {
    barcode?: string;
    type?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
}) => {
    return api.get<TransactionResponse>('/transactions/', { params });
};

// 删除商品
export const deleteInventory = (barcode: string) => {
    return api.delete<{ message: string }>(`/inventory/${barcode}`);
};

// 业绩统计相关类型定义
export interface ProfitRanking {
    barcode: string;
    name: string;
    total_cost: number;
    total_revenue: number;
    profit: number;
    profit_rate: number;
}

export interface SalesRanking {
    barcode: string;
    name: string;
    quantity: number;
    revenue: number;
}

export interface SalesSummary {
    total_purchase: number;
    total_sales: number;
    total_profit: number;
    profit_rate: number;
}

export interface PerformanceStats {
    profit_rankings: ProfitRanking[];
    sales_rankings: SalesRanking[];
    summary: SalesSummary;
}

// 业绩统计 API
export const getPerformanceStats = (params?: { start_date?: string; end_date?: string }) => {
    return api.get<PerformanceStats>('/performance/', { params });
};

export interface HotProduct {
    barcode: string;
    name: string;
    quantity: number;
    revenue: number;
} 