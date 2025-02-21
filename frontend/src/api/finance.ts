import api from './config';
import type { OtherTransaction, CreateOtherTransactionRequest, TransactionQueryParams } from '@/types/finance';
import type { PaginatedResponse } from '@/types/common';

// 获取收支记录列表
export const getTransactions = (params: TransactionQueryParams) => {
    return api.get<PaginatedResponse<OtherTransaction>>('/api/v1/finance/transactions', { params });
};

// 创建收支记录
export const createTransaction = (data: CreateOtherTransactionRequest) => {
    return api.post<OtherTransaction>('/api/v1/finance/transactions', data);
};

// 获取收支类型选项
export const getTypeOptions = () => {
    return [
        { label: '收入', value: 'income' },
        { label: '支出', value: 'expense' }
    ];
};

// 删除收支记录
export const deleteTransaction = (id: number) => {
    return api.delete<{ message: string }>(`/api/v1/finance/transactions/${id}`);
}; 