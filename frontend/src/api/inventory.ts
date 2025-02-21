import api from './config';
import type { Inventory } from '@/types/inventory';

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
    company: {
        id: number;
        name: string;
    };
    company_name?: string;
    notes?: string;
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

// 添加分页查询参数接口
export interface InventoryQueryParams {
    page: number;
    page_size: number;
    search?: string;
}

// 添加分页响应接口
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
}

// 修改获取库存列表的方法
export const getInventoryList = async (params: InventoryQueryParams): Promise<PaginatedResponse<Inventory>> => {
    const response = await api.get<PaginatedResponse<Inventory>>('/api/v1/inventory', { params });
    return response;
};

// 根据条形码获取商品
export const getInventoryByBarcode = (barcode: string) => {
    return api.get<Inventory>(`/api/v1/inventory/barcode/${barcode}`);
};

// 根据ID获取商品
export const getInventory = (id: number) => {
    return api.get<Inventory>(`/api/v1/inventory/id/${id}`);
};

// 创建商品
export const createInventory = async (data: Partial<Inventory>) => {
    try {
        const response = await api.post<Inventory>('/api/v1/inventory/', data);
        return response;
    } catch (error: any) {
        // 获取后端返回的具体错误信息
        const errorMessage = error.response?.data?.detail || '添加商品失败';
        throw new Error(errorMessage);
    }
};

// 更新商品
export const updateInventory = async (barcode: string, data: Partial<Inventory>) => {
    try {
        const response = await api.put<Inventory>(`/api/v1/inventory/${barcode}`, data);
        return response;
    } catch (error: any) {
        // 获取后端返回的具体错误信息
        const errorMessage = error.response?.data?.detail || '更新商品失败';
        throw new Error(errorMessage);
    }
};

// 商品入库
export const stockIn = (data: {
    barcode: string;
    quantity: number;
    price: number;
    company_id: number;
    notes?: string;
}) => {
    return api.post<Inventory>('/api/v1/inventory/stock-in', data);
};

// 商品出库
export const stockOut = (data: {
    barcode: string;
    quantity: number;
    price: number;
    company_id: number;
    notes?: string;
}) => {
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
    company_id?: number;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
}) => {
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
export const getProductAnalysis = (
    barcode: string,
    params: {
        start_date: string;
        end_date: string;
    }
) => {
    return api.get<ProductAnalysis>(`/api/v1/analysis/${barcode}`, { params });
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
    return api.get<Inventory[]>(`/api/v1/inventory/search/${searchText}`);
};

// 撤销交易记录
export const cancelTransaction = (transactionId: number) => {
    return api.delete<Inventory>(`/api/v1/transactions/${transactionId}`);
};

export interface StockInRecord {
    id: number;
    barcode: string;
    quantity: number;
    price: number;
    company: {
        id: number;
        name: string;
    };
} 