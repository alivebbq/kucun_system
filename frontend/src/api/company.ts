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
export const createCompany = (data: Partial<Company>) => {
    return api.post<Company>('/api/v1/companies/', data);
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
export const createPayment = (data: {
    company_id: number;
    amount: number;
    type: 'receive' | 'pay';
    notes?: string;
}) => {
    return api.post<Payment>('/api/v1/payments/', data);
};

// 获取收付款记录
export const getPayments = (companyId?: number) => {
    return api.get<Payment[]>('/api/v1/payments/', {
        params: { company_id: companyId }
    });
};

// 获取公司交易记录
export const getCompanyTransactions = (
    companyId: number,
    params?: {
        type?: string;
        skip?: number;
        limit?: number;
    }
) => {
    return api.get<{
        items: CompanyTransaction[];
        total: number;
    }>(`/api/v1/companies/${companyId}/transactions`, { params });
};

// 添加更新公司信息的接口
export const updateCompany = (id: number, data: Partial<Company>) => {
    return api.put<Company>(`/api/v1/companies/${id}`, data);
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