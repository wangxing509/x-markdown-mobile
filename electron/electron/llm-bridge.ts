import { exec } from 'child_process'
import { promisify } from 'util'
import os from 'os'
import http from 'http'
import https from 'https'
import fs from 'fs'
import path from 'path'

const execAsync = promisify(exec)

const IDE_PROCESS_NAMES = ['CodeBuddy.exe', 'WorkBuddy.exe', 'Code.exe', 'Cursor.exe']
const LLM_PORT_CANDIDATES = [9886, 11434, 3000, 5000]
const LLM_CONFIG_PATH = path.join(os.homedir(), '.xmarkdown', 'llm.json')

interface LlmConfig {
  provider: 'local' | 'api'
  apiBase: string
  apiKey: string
  model: string
  temperature: number
}

function readLlmConfig(): LlmConfig {
  const defaults: LlmConfig = {
    provider: 'local',
    apiBase: '',
    apiKey: '',
    model: 'deepseek-chat',
    temperature: 0.2,
  }
  try {
    if (fs.existsSync(LLM_CONFIG_PATH)) {
      const data = JSON.parse(fs.readFileSync(LLM_CONFIG_PATH, 'utf-8'))
      return { ...defaults, ...data }
    }
  } catch (e) {
    console.error('[LlmBridge] 读取 llm.json 失败:', e)
  }
  return defaults
}

export class LlmBridge {
  private ideDetected: boolean = false
  private llmPort: number | null = null
  private isOllama: boolean = false

  async detectIde() {
    if (os.platform() === 'win32') {
      try {
        const { stdout } = await execAsync('tasklist /fo csv /nh', { maxBuffer: 10 * 1024 * 1024 })
        for (const name of IDE_PROCESS_NAMES) {
          if (stdout.includes(name)) {
            console.log(`[LlmBridge] 检测到 IDE 进程: ${name}`)
            this.ideDetected = true
            break
          }
        }
      } catch (e) {
        console.error('[LlmBridge] 进程检测失败:', e)
      }
    }

    for (const port of LLM_PORT_CANDIDATES) {
      if (await this.probePort(port)) {
        this.llmPort = port
        if (port === 11434) this.isOllama = true
        console.log(`[LlmBridge] 检测到本地 LLM 端口: ${port}${this.isOllama ? ' (Ollama)' : ''}`)
        break
      }
    }

    const cfg = readLlmConfig()
    if (cfg.provider === 'api' && cfg.apiKey && cfg.apiBase) {
      console.log('[LlmBridge] 已配置 LLM API 通道')
    } else if (!this.ideDetected && !this.llmPort) {
      console.warn('[LlmBridge] 未检测到 IDE/本地 LLM，翻译/对话将降级')
    }
  }

  private probePort(port: number): Promise<boolean> {
    return new Promise((resolve) => {
      const req = http.get(`http://127.0.0.1:${port}/`, (res) => {
        resolve(res.statusCode !== undefined)
        res.destroy()
      })
      req.on('error', () => resolve(false))
      req.setTimeout(1000, () => {
        req.destroy()
        resolve(false)
      })
    })
  }

  isAvailable(): boolean {
    const cfg = readLlmConfig()
    return (
      (cfg.provider === 'api' && !!cfg.apiKey && !!cfg.apiBase) ||
      this.ideDetected ||
      this.llmPort !== null
    )
  }

  getStatus() {
    const cfg = readLlmConfig()
    return {
      ideDetected: this.ideDetected,
      llmPort: this.llmPort,
      isOllama: this.isOllama,
      apiConfigured: cfg.provider === 'api' && !!cfg.apiKey && !!cfg.apiBase,
      available: this.isAvailable(),
    }
  }

  /** 轻量译文质量检查：中文占比过低或疑似截断则需重试 */
  private checkQuality(original: string, translated: string): { ok: boolean; reason: string } {
    if (!translated || !translated.trim()) return { ok: false, reason: '空结果' }
    const cjk = (translated.match(/[\u4e00-\u9fff]/g) || []).length
    const alpha = (translated.match(/[a-zA-Z]/g) || []).length
    const total = cjk + alpha
    const cnRatio = total > 0 ? cjk / total : 0
    const lengthRatio = translated.length / Math.max(1, original.length)
    if (cnRatio < 0.2) return { ok: false, reason: `中文占比过低(${cnRatio.toFixed(2)})` }
    if (lengthRatio < 0.15) return { ok: false, reason: '疑似截断' }
    return { ok: true, reason: '' }
  }

  private async callApi(prompt: string, temperature: number): Promise<string> {
    const cfg = readLlmConfig()
    if (cfg.provider !== 'api' || !cfg.apiKey || !cfg.apiBase) {
      throw new Error('未配置 LLM API 通道')
    }
    const base = cfg.apiBase.replace(/\/+$/, '')
    const url = new URL(base + '/chat/completions')
    const data = JSON.stringify({
      model: cfg.model || 'default',
      messages: [{ role: 'user', content: prompt }],
      stream: false,
      temperature: temperature ?? cfg.temperature ?? 0.2,
    })
    const transport = url.protocol === 'https:' ? https : http
    return new Promise((resolve, reject) => {
      const req = transport.request(
        {
          hostname: url.hostname,
          port: url.port || (url.protocol === 'https:' ? 443 : 80),
          path: url.pathname,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${cfg.apiKey}`,
            'Content-Length': Buffer.byteLength(data),
          },
        },
        (res) => {
          let body = ''
          res.on('data', (c) => { body += c })
          res.on('end', () => {
            try {
              const json = JSON.parse(body)
              const content = json.choices?.[0]?.message?.content
              if (content) resolve(content.trim())
              else reject(new Error(`LLM API 返回为空: ${body.slice(0, 200)}`))
            } catch (e) {
              reject(new Error('LLM API 响应解析失败: ' + (e as Error).message))
            }
          })
        }
      )
      req.on('error', reject)
      req.setTimeout(120000, () => {
        req.destroy()
        reject(new Error('LLM API 请求超时'))
      })
      req.write(data)
      req.end()
    })
  }

  /**
   * 调用 LLM 翻译（三级通道：API → IDE → Ollama）
   * 含质量校验，失败时降温度重试一次
   */
  async translate(text: string, targetLang = 'zh-CN'): Promise<string> {
    const cfg = readLlmConfig()
    const buildPrompt = (temperature: number) =>
      `你是一个专业的翻译引擎。请将下面的内容翻译成${targetLang === 'zh-CN' ? '简体中文' : targetLang}。
要求：
1. 仅输出译文，不要任何解释或前后缀；
2. 保持原有的 Markdown 结构（标题、列表、代码块、表格、链接）；
3. 不要翻译代码块内容、URL、命令行、变量名；
4. 译文通顺自然，符合中文技术表达习惯；
5. AI/审计专业术语使用规范中文表达（如 LLM→大语言模型(LLM)、RAG→检索增强生成(RAG)、continuous auditing→连续审计）。

待翻译内容：
${text}`

    let translated = ''
    let temperature = cfg.provider === 'api' ? (cfg.temperature ?? 0.2) : 0.2
    if (cfg.provider === 'api' && cfg.apiKey && cfg.apiBase) {
      translated = await this.callApi(buildPrompt(temperature), temperature)
    } else if (this.isOllama && this.llmPort) {
      translated = await this.callOllama(buildPrompt(temperature), 'qwen2.5:7b', temperature)
    } else if (this.llmPort) {
      translated = await this.callOpenAiCompatible(buildPrompt(temperature), targetLang, temperature)
    } else {
      throw new Error('LLM 不可用，请配置 LLM API 或启动 CodeBuddy/WorkBuddy/Ollama')
    }

    const quality = this.checkQuality(text, translated)
    if (!quality.ok) {
      // 重试一次（更低温度，更严格）
      console.warn('[翻译] 质量校验未通过，重试:', quality.reason)
      const retryTemp = Math.max(0.05, temperature - 0.1)
      if (cfg.provider === 'api' && cfg.apiKey && cfg.apiBase) {
        translated = await this.callApi(buildPrompt(retryTemp), retryTemp)
      } else if (this.isOllama && this.llmPort) {
        translated = await this.callOllama(buildPrompt(retryTemp), 'qwen2.5:7b', retryTemp)
      } else if (this.llmPort) {
        translated = await this.callOpenAiCompatible(buildPrompt(retryTemp), targetLang, retryTemp)
      }
    }
    return translated
  }

  /** 调用 OpenAI 兼容接口（IDE 内置 LLM / vLLM / LM Studio 等） */
  private callOpenAiCompatible(prompt: string, targetLang: string, temperature: number): Promise<string> {
    return new Promise((resolve, reject) => {
      const data = JSON.stringify({
        model: 'default',
        messages: [
          { role: 'system', content: '你是一个严谨的 Markdown 翻译器。' },
          { role: 'user', content: prompt },
        ],
        stream: false,
        temperature,
      })
      const req = http.request(
        {
          hostname: '127.0.0.1',
          port: this.llmPort!,
          path: '/v1/chat/completions',
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) },
        },
        (res) => {
          let body = ''
          res.on('data', (c) => { body += c })
          res.on('end', () => {
            try {
              const json = JSON.parse(body)
              const content = json.choices?.[0]?.message?.content
              if (content) resolve(content.trim())
              else reject(new Error('IDE LLM 返回为空'))
            } catch (e) {
              reject(new Error('IDE LLM 响应解析失败: ' + (e as Error).message))
            }
          })
        }
      )
      req.on('error', reject)
      req.setTimeout(120000, () => {
        req.destroy()
        reject(new Error('IDE LLM 请求超时'))
      })
      req.write(data)
      req.end()
    })
  }

  /** 调用本地 LLM 蒸馏 Skill */
  async distill(text: string, skillName: string): Promise<string> {
    const prompt = `你是一个 Skill 蒸馏专家。请将以下内容蒸馏为一个标准化、可直接使用的 Skill 文档。

要求：
1. 保留核心工作流、代码模板、最佳实践
2. 去除冗余叙述
3. 输出 Markdown 格式，包含 frontmatter（name, description, version, alwaysApply）
4. Skill 名称: ${skillName}

内容：
${text}`
    const cfg = readLlmConfig()
    if (cfg.provider === 'api' && cfg.apiKey && cfg.apiBase) {
      return this.callApi(prompt, cfg.temperature ?? 0.3)
    }
    if (this.isOllama && this.llmPort) {
      return this.callOllama(prompt, 'qwen2.5:7b', 0.3)
    }
    throw new Error('LLM 不可用，请配置 LLM API 或启动 CodeBuddy/WorkBuddy/Ollama')
  }

  async chat(message: string, context = '', systemPrompt = ''): Promise<string> {
    const sys = systemPrompt ||
      (context
        ? `你是知识库助手。以下是知识库相关内容，请基于它回答用户问题：\n\n${context}\n\n用户问题: ${message}`
        : `用户问题: ${message}`)
    const cfg = readLlmConfig()
    if (cfg.provider === 'api' && cfg.apiKey && cfg.apiBase) {
      return this.callApi(sys, cfg.temperature ?? 0.3)
    }
    if (this.isOllama && this.llmPort) {
      return this.callOllama(sys, 'qwen2.5:7b', 0.3)
    }
    if (this.llmPort) {
      return this.callOpenAiCompatible(sys, 'zh-CN', 0.3)
    }
    throw new Error('LLM 不可用，请配置 LLM API 或启动 CodeBuddy/WorkBuddy/Ollama')
  }

  private callOllama(prompt: string, model: string, temperature: number): Promise<string> {
    return new Promise((resolve, reject) => {
      const data = JSON.stringify({
        model,
        prompt,
        stream: false,
        options: { temperature, top_p: 0.9 },
      })
      const req = http.request(
        {
          hostname: '127.0.0.1',
          port: this.llmPort!,
          path: '/api/generate',
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) },
        },
        (res) => {
          let body = ''
          res.on('data', (c) => { body += c })
          res.on('end', () => {
            try {
              const json = JSON.parse(body)
              resolve(json.response || json.message?.content || body)
            } catch {
              resolve(body)
            }
          })
        }
      )
      req.on('error', reject)
      req.setTimeout(60000, () => {
        req.destroy()
        reject(new Error('Ollama 请求超时'))
      })
      req.write(data)
      req.end()
    })
  }
}
