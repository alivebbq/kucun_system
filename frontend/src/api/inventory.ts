import api from './config';

export interface Inventory {
    id: number;
    barcode: string;
    name: string;
    unit: string;
    avg_purchase_price: number;
    selling_price: number;
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

export interface InventoryStats {
    total_items: number;
    total_value: number;
    low_stock_items: number;
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
    return api.get<InventoryStats>('/inventory/stats');
};

// 获取交易记录
export const getTransactions = (params?: {
    barcode?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
}) => {
    return api.get<Transaction[]>('/transactions/', { params });
};

// 删除商品
export const deleteInventory = (barcode: string) => {
    return api.delete<{ message: string }>(`/inventory/${barcode}`);
}; 