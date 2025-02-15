import api from './config';

export interface Inventory {
    id: number;
    barcode: string;
    name: string;
    unit: string;
    stock: number;
    warning_stock: number;
    is_active: boolean;
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
    return api.get<Inventory[]>('/api/v1/inventory/', { params });
};

// 根据条形码获取商品
export const getInventoryByBarcode = (barcode: string) => {
    return api.get<Inventory>(`/api/v1/inventory/${barcode}`);
};

// 创建商品
export const createInventory = async (data: Partial<Inventory>) => {
    try {
        const response = await api.post<Inventory>('/api/v1/inventory/', data);
        return response;
    } catch (error: any) {
        throw error;
    }
};

// 更新商品
export const updateInventory = async (barcode: string, data: Partial<Inventory>) => {
    try {
        const response = await api.put<Inventory>(`/api/v1/inventory/${barcode}`, data);
        return response;
    } catch (error: any) {
        throw error;
    }
};

// 商品入库
export const stockIn = (data: { barcode: string; quantity: number; price: number }) => {
    return api.post<Inventory>('/api/v1/inventory/stock-in', data);
};

// 商品出库
export const stockOut = (data: { barcode: string; quantity: number; price: number }) => {
    return api.post<Inventory>('/api/v1/inventory/stock-out', data);
};

// 获取库存统计
export const getInventoryStats = () => {
    return api.get<InventoryStats>('/api/v1/stats');
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
    // 过滤掉空字符串参数
    const filteredParams = Object.fromEntries(
        Object.entries(params || {}).filter(([_, v]) => v != null && v !== '')
    );
    return api.get<TransactionResponse>('/api/v1/transactions', { params: filteredParams });
};

// 删除商品
export const deleteInventory = (barcode: string) => {
    return api.delete<{ message: string }>(`/api/v1/inventory/${barcode}`);
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
    total_sales_cost: number;
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
    return api.get<PerformanceStats>('/api/v1/performance/', { params });
};

export interface HotProduct {
    barcode: string;
    name: string;
    quantity: number;
    revenue: number;
}

// 商品分析相关类型定义
export interface PricePoint {
    date: string;
    cost: number;
    price: number;
}

export interface SalesPoint {
    date: string;
    sales: number;
    profit: number;
}

export interface ProductAnalysis {
    price_trends: PricePoint[];
    sales_analysis: SalesPoint[];
}

// 商品分析 API
export const getProductAnalysis = (barcode: string, months: number = 1) => {
    return api.get<ProductAnalysis>(`/api/v1/analysis/${barcode}`, {
        params: { months }
    });
};

// 切换商品状态
export const toggleInventoryStatus = async (barcode: string) => {
    try {
        const response = await api.put<Inventory>(`/api/v1/inventory/${barcode}/toggle`);
        return response;
    } catch (error: any) {
        throw error;
    }
};

// 搜索商品
export const searchInventory = (searchText: string) => {
    return api.get<Inventory>(`/api/v1/inventory/search/${searchText}`);
};

// 撤销交易记录
export const cancelTransaction = (transactionId: number) => {
    return api.delete<Inventory>(`/api/v1/transactions/${transactionId}`);
}; 