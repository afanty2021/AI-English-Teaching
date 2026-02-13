/**
 * 统一日志工具
 * 根据环境自动控制日志级别
 */

// 开发环境启用调试日志
const DEBUG_MODE = import.meta.env.DEV

/**
 * 获取调用位置的行号
 */
function getLineInfo(): string {
  const error = new Error()
  const stack = error.stack?.split('\n') || []
  // 栈结构: Error\n    at Logger.xxx (logger.ts:XX)\n    at ...
  const caller = stack[3]
  return caller ? caller.trim() : 'unknown'
}

/**
 * 格式化日志消息
 */
function formatMessage(
  level: string,
  tag: string,
  message: string,
  args: any[]
): string {
  const lineInfo = DEBUG_MODE ? ` [${getLineInfo()}]` : ''
  return `[${tag.toUpperCase()}] ${message}${lineInfo}`
}

/**
 * 主日志函数
 */
function log(level: string, tag: string, message: string, ...args: any[]): void {
  const formattedMsg = formatMessage(level, tag, message, args)

  switch (level) {
    case 'debug':
      if (DEBUG_MODE) {
        console.debug(formattedMsg, ...args)
      }
      break
    case 'info':
      console.info(formattedMsg, ...args)
      break
    case 'warn':
      console.warn(formattedMsg, ...args)
      break
    case 'error':
      console.error(formattedMsg, ...args)
      break
  }
}

/**
 * 便捷日志方法
 */
export const logger = {
  debug: (tag: string, message: string, ...args: any[]) =>
    log('debug', tag, message, ...args),

  info: (tag: string, message: string, ...args: any[]) =>
    log('info', tag, message, ...args),

  warn: (tag: string, message: string, ...args: any[]) =>
    log('warn', tag, message, ...args),

  error: (tag: string, message: string, ...args: any[]) =>
    log('error', tag, message, ...args),

  /**
   * 性能计时
   */
  time: (tag: string, label: string) => {
    if (DEBUG_MODE) {
      console.time(`${tag}:${label}`)
    }
  },

  timeEnd: (tag: string, label: string) => {
    if (DEBUG_MODE) {
      console.timeEnd(`${tag}:${label}`)
    }
  }
}

/**
 * 创建带标签的日志器
 */
export function createLogger(tag: string) {
  return {
    debug: (message: string, ...args: any[]) => logger.debug(tag, message, ...args),
    info: (message: string, ...args: any[]) => logger.info(tag, message, ...args),
    warn: (message: string, ...args: any[]) => logger.warn(tag, message, ...args),
    error: (message: string, ...args: any[]) => logger.error(tag, message, ...args),
    time: (label: string) => logger.time(tag, label),
    timeEnd: (label: string) => logger.timeEnd(tag, label)
  }
}

export default logger
