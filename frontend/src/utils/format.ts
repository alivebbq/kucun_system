/**
 * 格式化日期时间
 * @param date 日期时间字符串或Date对象
 * @returns 格式化后的日期时间字符串
 */
export const formatDateTime = (date: string | Date | undefined): string => {
    if (!date) return '-'

    const d = typeof date === 'string' ? new Date(date) : date

    // 如果日期无效
    if (isNaN(d.getTime())) return '-'

    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    const seconds = String(d.getSeconds()).padStart(2, '0')

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

/**
 * 格式化日期
 * @param date 日期字符串或Date对象
 * @returns 格式化后的日期字符串
 */
export const formatDate = (date: string | Date | undefined): string => {
    if (!date) return '-'

    const d = typeof date === 'string' ? new Date(date) : date

    // 如果日期无效
    if (isNaN(d.getTime())) return '-'

    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')

    return `${year}-${month}-${day}`
}

/**
 * 格式化金额
 * @param amount 金额数值
 * @param decimals 小数位数
 * @returns 格式化后的金额字符串
 */
export const formatAmount = (amount: number | undefined, decimals: number = 2): string => {
    if (amount === undefined || amount === null) return '¥0.00'

    return `¥${amount.toFixed(decimals)}`
}

/**
 * 格式化数量
 * @param quantity 数量
 * @returns 格式化后的数量字符串
 */
export const formatQuantity = (quantity: number | undefined): string => {
    if (quantity === undefined || quantity === null) return '0'

    return quantity.toString()
} 