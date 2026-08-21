import { app, BrowserWindow, shell } from 'electron'
import path from 'path'
import fs from 'fs'
import { registerIpcHandlers, setLlmBridge, setPythonStarted } from './ipc-handlers'
import { PythonManager } from './python-manager'
import { LlmBridge } from './llm-bridge'

let mainWindow: BrowserWindow | null = null
let pythonManager: PythonManager | null = null
let llmBridge: LlmBridge | null = null

// 判断是否为开发模式：检查是否有 Vite dev server 在运行
// 优先检查环境变量 DEV_SERVER_URL，其次检查 dist/index.html 是否存在
const distHtmlPath = path.join(app.getAppPath(), 'dist', 'index.html')
const useDevServer = !!process.env.DEV_SERVER_URL && !fs.existsSync(distHtmlPath)

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    title: 'X markdown',
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(app.getAppPath(), 'dist-electron', 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: false,
      allowRunningInsecureContent: true,
    },
  })

  // 加载页面并监听错误
  if (useDevServer) {
    mainWindow.loadURL(process.env.DEV_SERVER_URL!)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(distHtmlPath)
  }

  // 诊断：打印加载失败信息
  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    console.error(`[加载失败] code=${errorCode} desc=${errorDescription} url=${validatedURL}`)
  })

  mainWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    console.log(`[renderer:${level}] ${message} (${sourceId}:${line})`)
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // 确保是有效的外部 URL
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      shell.openExternal(url)
    }
    return { action: 'deny' }
  })

  // 防止应用内导航到外部链接
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url !== mainWindow?.webContents.getURL()) {
      event.preventDefault()
      if (url.startsWith('http://') || url.startsWith('https://')) {
        shell.openExternal(url)
      }
    }
  })
}

async function startBackend() {
  pythonManager = new PythonManager()
  await pythonManager.start()
  setPythonStarted(true)
}

app.whenReady().then(async () => {
  registerIpcHandlers()

  llmBridge = new LlmBridge()
  await llmBridge.detectIde()
  setLlmBridge(llmBridge)

  // 先创建窗口，后端在后台异步启动（避免阻塞窗口显示）
  createWindow()

  // 后台启动 Python 后端
  startBackend().catch((e) => {
    console.error('[主进程] 后端启动失败:', e)
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (pythonManager) {
    pythonManager.stop()
  }
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (pythonManager) {
    pythonManager.stop()
  }
})
