import api from './config'
import type { StockOrder, CreateStockOrderRequest } from '@/types/inventory'

// 获取出入库单列表
export const getStockOrders = (params: {
    page?: number
    limit?: number
    search?: string
    type?: string
    status?: string
}) => {
    // 确保所有参数都有默认值
    const defaultParams = {
        page: 1,
        limit: 20,
        search: '',
        type: '',
        status: ''
    };

    return api.get<{ items: StockOrder[]; total: number }>('/api/v1/stock-orders', {
        params: {
            ...defaultParams,
            ...params
        }
    });
}

// 获取出入库单详情
export const getStockOrder = (id: number) => {
    return api.get<StockOrder>(`/api/v1/stock-orders/${id}`);
}

// 创建出入库单
export const createStockOrder = async (data: CreateStockOrderRequest) => {
    try {
        const response = await api.post<StockOrder>('/api/v1/stock-orders', data);
        return response;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || '创建出入库单失败';
        throw new Error(errorMessage);
    }
};

// 确认出入库单
export const confirmStockOrder = (id: number) => {
    return api.post<StockOrder>(`/api/v1/stock-orders/${id}/confirm`)
}

// 取消出入库单
export const cancelStockOrder = (id: number) => {
    return api.post<StockOrder>(`/api/v1/stock-orders/${id}/cancel`)
}

// 更新出入库单
export const updateStockOrder = async (id: number, data: any) => {
    try {
        const response = await api.put<StockOrder>(`/api/v1/stock-orders/${id}`, data);
        return response;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || '更新出入库单失败';
        throw new Error(errorMessage);
    }
}; 