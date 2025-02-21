import api from './config';
import type { OtherTransaction, CreateOtherTransactionRequest, TransactionQueryParams, ProfitStatistics, PaymentRecord } from '@/types/finance';
import type { PaginatedResponse } from '@/api/inventory';
import { CompanyType } from '@/types/company';

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

// 获取利润统计
export const getProfitStatistics = (params: { start_date: string; end_date: string }) => {
    return api.get<ProfitStatistics>('/api/v1/finance/profit', { params });
};

// 获取其他收支明细
export const getOtherTransactions = (params: TransactionQueryParams) => {
    return api.get<{ items: OtherTransaction[]; total: number }>('/api/v1/finance/transactions', { params });
};

// 获取收付款记录
export const getPaymentRecords = (params: {
    start_date: string;
    end_date: string;
    company_type: CompanyType;
    page?: number;
    page_size?: number;
}) => {
    return api.get<{ items: PaymentRecord[]; total: number }>('/api/v1/finance/payment-records', { params });
}; 