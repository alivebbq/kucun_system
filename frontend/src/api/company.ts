import api from './config';
import type { Company, CompanyBalance, Payment, CompanyTransaction } from '../types/company';
import { CompanyType } from '../types/company';

// 获取公司列表
export const getCompanies = async (params?: { type?: CompanyType }) => {
    try {
        const response = await api.get<{ items: Company[]; total: number }>('/api/v1/companies', {
            params,
            // 添加错误重试
            retry: 3,
            retryDelay: 1000
        });
        console.log('Companies response:', response);
        return response;
    } catch (error) {
        console.error('Error fetching companies:', error);
        throw error;
    }
};

// 创建公司
export const createCompany = async (data: Partial<Company>) => {
    try {
        const response = await api.post<Company>('/api/v1/companies/', data);
        return response;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || '添加公司失败';
        throw new Error(errorMessage);
    }
};

// 获取应收应付情况
export const getCompanyBalances = (params?: {
    type?: CompanyType;
    skip?: number;
    limit?: number;
}) => {
    return api.get<{
        items: CompanyBalance[];
        total: number;
    }>('/api/v1/companies/balance', { params });
};

// 创建收付款记录
export const createPayment = async (data: {
    company_id: number;
    amount: number;
    type: 'receive' | 'pay';
    notes?: string;
}) => {
    try {
        const response = await api.post<Payment>('/api/v1/payments/', data);
        return response;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || '创建收付款记录失败';
        throw new Error(errorMessage);
    }
};

// 获取收付款记录
export const getPayments = (companyId?: number) => {
    return api.get<Payment[]>('/api/v1/payments/', {
        params: { company_id: companyId }
    });
};

// 获取公司交易记录
export const getCompanyTransactions = (companyId: number) => {
    return api.get<CompanyTransaction[]>(`/api/v1/companies/${companyId}/transactions`);
};

// 添加更新公司信息的接口
export const updateCompany = async (id: number, data: Partial<Company>) => {
    try {
        const response = await api.put<Company>(`/api/v1/companies/${id}`, data);
        return response;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || '更新公司信息失败';
        throw new Error(errorMessage);
    }
};

// 获取总应收应付金额
export const getCompanyTotalBalance = (type?: CompanyType) => {
    return api.get<{
        total_receivable: number;
        total_payable: number;
    }>('/api/v1/companies/total-balance', {
        params: { type }
    });
}; 