import { spawn, ChildProcess } from 'child_process'
import path from 'path'
import os from 'os'
import http from 'http'

const PYTHON_EXE = process.env.XMARKDOWN_PYTHON
  || (os.platform() === 'win32' ? 'C:\\Users\\qzq\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' : 'python3')

const BACKEND_PORT = 8765
const BACKEND_HOST = '127.0.0.1'

export class PythonManager {
  private process: ChildProcess | null = null
  private backendDir: string

  constructor() {
    this.backendDir = path.join(process.cwd(), 'backend')
  }

  async start() {
    // 先检测后端是否已经在运行
    const alive = await this.healthCheck(2000)
    if (alive) {
      console.log('[PythonManager] 后端已在运行，跳过启动')
      return
    }

    const env = {
      ...process.env,
      PYTHONIOENCODING: 'utf-8',
      PYTHONLEGACYWINDOWSSTDIO: 'utf-8',
    }

    const args = ['-m', 'uvicorn', 'main:app', '--host', BACKEND_HOST, '--port', String(BACKEND_PORT)]

    console.log(`[PythonManager] 启动后端: ${PYTHON_EXE} ${args.join(' ')}`)
    this.process = spawn(PYTHON_EXE, args, {
      cwd: this.backendDir,
      env,
      shell: false,
      stdio: ['ignore', 'pipe', 'pipe'],
    })

    this.process.stdout?.on('data', (chunk) => {
      const text = chunk.toString()
      console.log(`[backend] ${text.trim()}`)
    })

    this.process.stderr?.on('data', (chunk) => {
      const text = chunk.toString()
      console.error(`[backend:err] ${text.trim()}`)
    })

    this.process.on('exit', (code) => {
      console.log(`[PythonManager] 后端进程退出，code=${code}`)
      this.process = null
    })

    // 等待健康检查通过（最多 30 秒）
    const started = await this.waitForReady(30000)
    if (!started) {
      console.warn('[PythonManager] 后端未在 30 秒内就绪，继续尝试...')
    }
  }

  async stop() {
    if (!this.process) return
    try {
      // Windows 下发送 taskkill /pid
      if (os.platform() === 'win32') {
        const { execSync } = await import('child_process')
        execSync(`taskkill /pid ${this.process.pid} /f /t`, { stdio: 'ignore' })
      } else {
        this.process.kill('SIGTERM')
      }
    } catch (e) {
      console.error('[PythonManager] 停止失败:', e)
    }
    this.process = null
  }

  private healthCheck(timeoutMs: number): Promise<boolean> {
    return new Promise((resolve) => {
      const req = http.get(`http://${BACKEND_HOST}:${BACKEND_PORT}/api/health`, (res) => {
        resolve(res.statusCode === 200)
        res.destroy()
      })
      req.on('error', () => resolve(false))
      req.setTimeout(timeoutMs, () => {
        req.destroy()
        resolve(false)
      })
    })
  }

  private async waitForReady(timeoutMs: number) {
    const deadline = Date.now() + timeoutMs
    while (Date.now() < deadline) {
      if (await this.healthCheck(2000)) {
        return true
      }
      await new Promise((r) => setTimeout(r, 1000))
    }
    return false
  }
}
