/**
 * 浏览器兼容性检测工具
 * 支持Web Speech API、Web Audio API和WASM检测
 */

export interface BrowserInfo {
  engine: 'chrome' | 'firefox' | 'safari' | 'edge' | 'unknown'
  version: string
  webSpeechSupported: boolean
  webAudioSupported: boolean
  wasmSupported: boolean
  isSecureContext: boolean
  userAgent: string
}

export interface CompatibilityResult {
  isSupported: boolean
  score: number
  recommendations: string[]
  warnings: string[]
  engine: BrowserInfo
}

/**
 * 浏览器兼容性检测类
 */
export class BrowserCompatibility {
  /**
   * 检测当前浏览器信息
   */
  static detect(): BrowserInfo {
    const ua = navigator.userAgent
    const vendor = navigator.vendor || ''

    // 检测引擎类型 - 注意顺序，先检测Edge再检测Chrome
    let engine: BrowserInfo['engine'] = 'unknown'
    if (/Edg/.test(ua)) {
      engine = 'edge'
    } else if (/Chrome/.test(ua) && /Google Inc/.test(vendor)) {
      engine = 'chrome'
    } else if (/Firefox/.test(ua)) {
      engine = 'firefox'
    } else if (/Safari/.test(ua) && /Apple Computer/.test(vendor)) {
      engine = 'safari'
    }

    // 获取版本号
    const version = this.getVersion(ua, engine)

    return {
      engine,
      version,
      webSpeechSupported: this.checkWebSpeechSupport(),
      webAudioSupported: this.checkWebAudioSupport(),
      wasmSupported: this.checkWasmSupport(),
      isSecureContext: this.checkSecureContext(),
      userAgent: ua
    }
  }

  /**
   * 检查Web Speech API支持
   */
  private static checkWebSpeechSupport(): boolean {
    return !!(
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition
    )
  }

  /**
   * 检查Web Audio API支持
   */
  private static checkWebAudioSupport(): boolean {
    return !!(
      window.AudioContext ||
      (window as any).webkitAudioContext
    )
  }

  /**
   * 检查WASM支持
   */
  private static checkWasmSupport(): boolean {
    return typeof WebAssembly === 'object' && WebAssembly !== null
  }

  /**
   * 检查安全上下文
   */
  private static checkSecureContext(): boolean {
    return window.isSecureContext || location.protocol === 'https:'
  }

  /**
   * 提取浏览器版本
   */
  private static getVersion(ua: string, engine: BrowserInfo['engine']): string {
    if (engine === 'unknown') {
      return 'unknown'
    }

    let match: RegExpMatchArray | null = null
    switch (engine) {
      case 'chrome':
        match = ua.match(/Chrome\/(\d+)/i)
        break
      case 'firefox':
        match = ua.match(/Firefox\/(\d+)/i)
        break
      case 'safari':
        match = ua.match(/Version\/(\d+)/i)
        break
      case 'edge':
        match = ua.match(/Edg\/(\d+)/i)
        break
    }
    return match ? match[1] ?? 'unknown' : 'unknown'
  }

  /**
   * 获取兼容性评分 (0-100)
   */
  static getCompatibilityScore(browser: BrowserInfo): number {
    let score = 0

    // Web Speech API 支持 (40分)
    if (browser.webSpeechSupported) {
      score += 40
    }

    // Web Audio API 支持 (30分)
    if (browser.webAudioSupported) {
      score += 30
    }

    // WASM 支持 (20分)
    if (browser.wasmSupported) {
      score += 20
    }

    // 安全上下文 (10分)
    if (browser.isSecureContext) {
      score += 10
    }

    return score
  }

  /**
   * 获取兼容性结果
   */
  static getCompatibilityResult(): CompatibilityResult {
    const engine = this.detect()
    const score = this.getCompatibilityScore(engine)

    const recommendations: string[] = []
    const warnings: string[] = []

    // 生成建议和警告
    if (!engine.webSpeechSupported) {
      warnings.push('当前浏览器不支持Web Speech API')
      recommendations.push('建议使用Chrome、Firefox或Edge浏览器')
    }

    if (!engine.webAudioSupported) {
      warnings.push('当前浏览器不支持Web Audio API')
    }

    if (!engine.isSecureContext) {
      warnings.push('当前页面不是安全上下文，语音功能可能受限')
      recommendations.push('请使用HTTPS协议访问')
    }

    if (engine.engine === 'safari') {
      recommendations.push('Safari浏览器对语音识别支持有限，可能需要降级处理')
    }

    // 引擎特定建议
    if (engine.engine === 'chrome' || engine.engine === 'edge') {
      recommendations.push('推荐使用，语音识别支持最佳')
    } else if (engine.engine === 'firefox') {
      recommendations.push('需要polyfill支持，建议更新到最新版本')
    }

    return {
      isSupported: score >= 50,
      score,
      recommendations,
      warnings,
      engine
    }
  }

  /**
   * 检查浏览器是否支持语音识别
   */
  static isVoiceRecognitionSupported(): boolean {
    const result = this.getCompatibilityResult()
    return result.isSupported
  }

  /**
   * 获取推荐的浏览器
   */
  static getRecommendedBrowsers(): string[] {
    return [
      'Chrome 90+',
      'Edge 90+',
      'Firefox 88+ (需要polyfill)',
      'Safari 14+ (有限支持)'
    ]
  }

  /**
   * 生成兼容性报告
   */
  static generateReport(): string {
    const result = this.getCompatibilityResult()
    const { engine, score } = result

    return `
浏览器兼容性报告
================
浏览器: ${engine.engine} ${engine.version}
兼容性评分: ${score}/100

功能支持:
  Web Speech API: ${engine.webSpeechSupported ? '✅' : '❌'}
  Web Audio API: ${engine.webAudioSupported ? '✅' : '❌'}
  WASM支持: ${engine.wasmSupported ? '✅' : '❌'}
  安全上下文: ${engine.isSecureContext ? '✅' : '❌'}

${result.warnings.length > 0 ? '警告:\n' + result.warnings.map(w => `  ⚠️ ${w}`).join('\n') + '\n' : ''}
${result.recommendations.length > 0 ? '建议:\n' + result.recommendations.map(r => `  💡 ${r}`).join('\n') : ''}
`
  }
}

/**
 * 导出便利函数
 */
export const browserCompatibility = BrowserCompatibility
export default BrowserCompatibility
