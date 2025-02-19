export enum CompanyType {
    SUPPLIER = 'SUPPLIER',
    CUSTOMER = 'CUSTOMER'
}

export interface Company {
    id: number;
    name: string;
    type: CompanyType;  // 使用 CompanyType 枚举
    contact?: string;
    phone?: string;
    address?: string;
    created_at: string;
}

export interface CompanyBalance {
    company: Company;
    receivable: number;  // 应收
    payable: number;    // 应付
    balance: number;    // 净额
}

export interface Payment {
    id: number;
    company_id: number;
    amount: number;
    type: 'receive' | 'pay';
    notes?: string;
    created_at: string;
    company: Company;
}

export interface CompanyTransaction {
    id: number;
    type: 'stock_in' | 'stock_out' | 'receive' | 'pay';
    amount: number;
    timestamp: string;
    notes?: string;
    operator_name: string;
} 