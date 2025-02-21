export enum TransactionType {
    INCOME = 'income',
    EXPENSE = 'expense'
}

export interface OtherTransaction {
    id: number;
    type: TransactionType;
    amount: number;
    transaction_date: string;  // YYYY-MM-DD 格式
    notes?: string;
    operator_id: number;
    operator_name?: string;
    created_at: string;
    updated_at: string;
}

export interface CreateOtherTransactionRequest {
    type: TransactionType;
    amount: number;
    transaction_date: string;  // YYYY-MM-DD 格式
    notes?: string;
}

export interface TransactionQueryParams {
    page?: number;
    page_size?: number;
    type?: TransactionType;
    start_date?: string;
    end_date?: string;
}

export interface ProfitStatistics {
    received_payments: number;
    other_income: number;
    total_income: number;
    paid_payments: number;
    other_expense: number;
    total_expense: number;
    profit: number;
}


export interface PaymentRecord {
    payment_date: string;
    company_name: string;
    amount: number;
    notes?: string;
    operator_name: string;
} 