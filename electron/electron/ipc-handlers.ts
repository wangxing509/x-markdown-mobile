import { ipcMain, clipboard, dialog, app, BrowserWindow } from 'electron'
import fs from 'fs'
import path from 'path'
import os from 'os'
import type { LlmBridge } from './llm-bridge'

const KB_DIR = path.join(os.homedir(), '.xmarkdown', 'knowledge-base')
const SKILLS_DIR = path.join(os.homedir(), '.codebuddy', 'skills')
const PROXY_CONFIG_PATH = path.join(os.homedir(), '.xmarkdown', 'proxy.json')

function normalizeProxyUrl(url: string): string {
  url = (url || '').trim()
  if (url && !url.startsWith('http')) {
    url = 'http://' + url
  }
  return url
}

function ensureDir(dir: string) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true })
  }
}

// LLM 桥接实例引用（由 main.ts 注入）
let _llmBridge: LlmBridge | null = null
let _pythonStarted = false

export function setLlmBridge(bridge: LlmBridge) {
  _llmBridge = bridge
}

export function setPythonStarted(started: boolean) {
  _pythonStarted = started
}

export function registerIpcHandlers() {
  ensureDir(KB_DIR)
  ensureDir(SKILLS_DIR)

  // ====== 文件保存（带对话框） ======
  ipcMain.handle('show-save-dialog', async (_event, defaultName: string) => {
    const result = await dialog.showSaveDialog({
      title: '保存 Markdown 文件',
      defaultPath: path.join(app.getPath('downloads'), defaultName || 'untitled.md'),
      filters: [
        { name: 'Markdown', extensions: ['md'] },
        { name: '所有文件', extensions: ['*'] },
      ],
    })
    return result.canceled ? null : result.filePath
  })

  ipcMain.handle('save-markdown', async (_event, filename: string, content: string) => {
    ensureDir(KB_DIR)
    const filepath = path.join(KB_DIR, filename)
    fs.writeFileSync(filepath, content, 'utf-8')
    return filepath
  })

  ipcMain.handle('save-markdown-to-path', async (_event, filepath: string, content: string) => {
    fs.writeFileSync(filepath, content, 'utf-8')
    return filepath
  })

  ipcMain.handle('read-markdown', async (_event, filepath: string) => {
    if (!fs.existsSync(filepath)) return null
    return fs.readFileSync(filepath, 'utf-8')
  })

  // ====== 知识库列表 ======
  ipcMain.handle('list-kb', async () => {
    ensureDir(KB_DIR)
    const result: Array<{ name: string; path: string; size: number; modified: string }> = []
    const entries = fs.readdirSync(KB_DIR)
    for (const entry of entries) {
      const fullPath = path.join(KB_DIR, entry)
      const stat = fs.statSync(fullPath)
      if (stat.isFile() && entry.endsWith('.md')) {
        result.push({
          name: entry.replace(/\.md$/, ''),
          path: fullPath,
          size: stat.size,
          modified: stat.mtime.toISOString(),
        })
      }
    }
    result.sort((a, b) => b.modified.localeCompare(a.modified))
    return result
  })

  // ====== 剪贴板 ======
  ipcMain.handle('copy-clipboard', async (_event, text: string) => {
    clipboard.writeText(text)
    return true
  })

  // ====== Skill 导出 ======
  ipcMain.handle('export-skill', async (_event, skillName: string, content: string) => {
    const skillDir = path.join(SKILLS_DIR, skillName)
    ensureDir(skillDir)
    const skillPath = path.join(skillDir, 'SKILL.md')
    fs.writeFileSync(skillPath, content, 'utf-8')
    return skillPath
  })

  // ====== LLM 桥接 ======
  ipcMain.handle('llm-translate', async (_event, text: string, targetLang: string) => {
    if (!_llmBridge) throw new Error('LLM 桥接未初始化')
    return _llmBridge.translate(text, targetLang)
  })

  ipcMain.handle('llm-distill', async (_event, text: string, skillName: string) => {
    if (!_llmBridge) throw new Error('LLM 桥接未初始化')
    return _llmBridge.distill(text, skillName)
  })

  ipcMain.handle('llm-chat', async (_event, message: string, context: string, systemPrompt?: string) => {
    if (!_llmBridge) throw new Error('LLM 桥接未初始化')
    return _llmBridge.chat(message, context, systemPrompt)
  })

  ipcMain.handle('llm-status', async () => {
    if (!_llmBridge) return { available: false }
    return _llmBridge.getStatus()
  })

  // ====== 后端状态 ======
  ipcMain.handle('backend-status', async () => {
    return { started: _pythonStarted, port: 8765 }
  })

  // ====== PDF 导出（隐藏窗口渲染 + printToPDF） ======
  ipcMain.handle('export-pdf', async (_event, html: string, defaultName: string) => {
    const result = await dialog.showSaveDialog({
      title: '导出 PDF',
      defaultPath: path.join(app.getPath('downloads'), defaultName || 'untitled.pdf'),
      filters: [{ name: 'PDF', extensions: ['pdf'] }],
    })
    if (result.canceled || !result.filePath) return null

    const win = new BrowserWindow({
      show: false,
      webPreferences: { sandbox: true },
    })
    try {
      await win.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html))
      const pdf = await win.webContents.printToPDF({
        pageSize: 'A4',
        printBackground: true,
        margins: { top: 0.6, bottom: 0.6, left: 0.6, right: 0.6 },
      })
      fs.writeFileSync(result.filePath, pdf)
      return result.filePath
    } catch (e) {
      console.error('[导出PDF] 失败:', e)
      return null
    } finally {
      win.destroy()
    }
  })

  // ====== 代理配置（本地文件，不依赖 Python 后端）======
  ipcMain.handle('get-proxy', async () => {
    try {
      if (fs.existsSync(PROXY_CONFIG_PATH)) {
        const data = JSON.parse(fs.readFileSync(PROXY_CONFIG_PATH, 'utf-8'))
        return { enabled: !!data.enabled, url: data.url || '' }
      }
    } catch (e) {
      console.error('[代理] 读取失败:', e)
    }
    return { enabled: false, url: '' }
  })

  ipcMain.handle('set-proxy', async (_event, enabled: boolean, url: string) => {
    const normalized = normalizeProxyUrl(url)
    ensureDir(path.dirname(PROXY_CONFIG_PATH))
    fs.writeFileSync(
      PROXY_CONFIG_PATH,
      JSON.stringify({ enabled: !!enabled, url: normalized }, null, 2),
      'utf-8'
    )
    return { enabled: !!enabled, url: normalized }
  })
}
