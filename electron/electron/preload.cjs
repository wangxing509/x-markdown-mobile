const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('xmarkdown', {
  // 文件操作
  saveMarkdown: (filename, content) => ipcRenderer.invoke('save-markdown', filename, content),
  saveMarkdownToPath: (filepath, content) => ipcRenderer.invoke('save-markdown-to-path', filepath, content),
  readMarkdown: (filepath) => ipcRenderer.invoke('read-markdown', filepath),
  listKnowledgeBase: () => ipcRenderer.invoke('list-kb'),

  // 剪贴板
  copyToClipboard: (text) => ipcRenderer.invoke('copy-clipboard', text),

  // 文件对话框
  showSaveDialog: (defaultName) => ipcRenderer.invoke('show-save-dialog', defaultName),

  // LLM 桥接
  llmTranslate: (text, targetLang) => ipcRenderer.invoke('llm-translate', text, targetLang),
  llmDistill: (text, skillName) => ipcRenderer.invoke('llm-distill', text, skillName),
  llmChat: (message, context, systemPrompt) => ipcRenderer.invoke('llm-chat', message, context, systemPrompt),
  llmStatus: () => ipcRenderer.invoke('llm-status'),

  // PDF 导出
  exportPdf: (html, defaultName) => ipcRenderer.invoke('export-pdf', html, defaultName),

  // Skill 导出
  exportSkill: (skillName, content) => ipcRenderer.invoke('export-skill', skillName, content),

  // Python 后端状态
  backendStatus: () => ipcRenderer.invoke('backend-status'),

  // 代理配置（本地文件，不依赖 Python 后端）
  getProxy: () => ipcRenderer.invoke('get-proxy'),
  setProxy: (enabled, url) => ipcRenderer.invoke('set-proxy', enabled, url),
})
