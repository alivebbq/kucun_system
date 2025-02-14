import api from './config';

export interface OperationLog {
    id: number;
    operation_type: string;
    operator: {
        id: number;
        name: string;
    };
    details: any;
    created_at: string;
}

export const getOperationLogs = (params?: {
    start_date?: string;
    end_date?: string;
    operation_type?: string;
}) => {
    return api.get<OperationLog[]>('/api/v1/logs', { params });
}; 