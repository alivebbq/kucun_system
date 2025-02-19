// 出入库单状态
export type OrderStatus = 'draft' | 'confirmed' | 'cancelled'

// 出入库单明细
export interface StockOrderItem {
    id: number
    inventory_id: number
    barcode: string
    quantity: number
    price: number
    total: number
    notes?: string
}

// 出入库单
export interface StockOrder {
    id: number
    order_no: string
    type: 'in' | 'out'
    company_id: number
    company_name: string
    total_amount: number
    operator_id: number
    operator_name: string
    store_id: number
    status: OrderStatus
    notes?: string
    created_at: string
    updated_at?: string
    items: StockOrderItem[]
}

// 创建出入库单请求
export interface CreateStockOrderRequest {
    type: 'in' | 'out'
    company_id: number
    notes?: string
    items: {
        inventory_id: number
        barcode: string
        quantity: number
        price: number
        notes?: string
    }[]
} 