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