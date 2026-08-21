#!/usr/bin/env node
/**
 * 通过 GitHub REST API（api.github.com）快速推送本地文件到仓库。
 * 使用 Node 原生 fetch + 并发 blobs + 递归目录树，绕过被限制的 git-over-https。
 *
 * 依赖: gh CLI 已登录（api.github.com 可达）。token 通过 `gh auth token` 获取。
 * 用法: node scripts/push-via-api.mjs --repo owner/repo [--branch main] [--dir <path>] [--jobs N]
 */
import { execSync } from 'node:child_process'
import { readFileSync, statSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { glob } from 'node:fs/promises'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const args = process.argv.slice(2)
function argVal(name) {
  const i = args.findIndex((a) => a === `--${name}`)
  return i >= 0 ? args[i + 1] : null
}
const repo = argVal('repo')
const branch = argVal('branch') || 'main'
const dir = argVal('dir') || path.resolve(__dirname, '..')
const CONCURRENCY = parseInt(argVal('jobs') || '6', 10)

if (!repo) {
  console.error('请提供 --repo owner/repo')
  process.exit(1)
}

const token = execSync('gh auth token', { encoding: 'utf8' }).trim()
const API = 'https://api.github.com'
const HEADERS = {
  Authorization: `Bearer ${token}`,
  Accept: 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28',
  'Content-Type': 'application/json',
}

async function api(method, endpoint, payload, _retries = 8) {
  const url = `${API}${endpoint}`
  for (let attempt = 0; attempt <= _retries; attempt++) {
    let res
    try {
      res = await fetch(url, {
        method,
        headers: HEADERS,
        body: payload ? JSON.stringify(payload) : undefined,
      })
    } catch (e) {
      if (attempt === _retries) throw e
      await new Promise((r) => setTimeout(r, 2000 * (attempt + 1)))
      continue
    }
    if (!res.ok) {
      const text = await res.text()
      if ((res.status === 403 && text.includes('secondary rate limit')) ||
          res.status === 429 || res.status >= 500) {
        if (attempt === _retries) {
          throw new Error(`${method} ${endpoint} ${res.status}: ${text.slice(0, 200)}`)
        }
        await new Promise((r) => setTimeout(r, 3000 * (attempt + 1)))
        continue
      }
      throw new Error(`${method} ${endpoint} ${res.status}: ${text.slice(0, 300)}`)
    }
    return res.status === 204 ? null : res.json()
  }
}

// 收集文件
const files = []
for await (const p of glob('**/*', { cwd: dir, dot: true })) {
  const abs = path.join(dir, p)
  let st
  try { st = statSync(abs) } catch { continue }
  if (!st.isFile()) continue
  const rel = p.split(path.sep).join('/')
  if (rel.startsWith('.git/')) continue
  if (rel.split('/').some((x) => ['node_modules', 'dist', 'dist-electron', 'release', '__pycache__', '.tmp-gh-pages'].includes(x))) continue
  if (rel.endsWith('.db')) continue
  files.push({ rel, abs })
}
console.log(`共 ${files.length} 个文件待推送`)

// 分支基提交
let baseSha = null
try {
  baseSha = (await api('GET', `/repos/${repo}/git/ref/heads/${branch}`)).object.sha
  console.log(`分支 ${branch} 已存在，基于 ${baseSha.slice(0, 7)} 更新`)
} catch {
  console.log(`分支 ${branch} 不存在，将创建初始提交`)
}

// 1. 并发创建所有 blobs
const blobByRel = new Map()
let done = 0
async function blobWorker(start) {
  for (let i = start; i < files.length; i += CONCURRENCY) {
    const f = files[i]
    const content = readFileSync(f.abs).toString('base64')
    const blob = await api('POST', `/repos/${repo}/git/blobs`, { content, encoding: 'base64' })
    blobByRel.set(f.rel, { path: f.rel, mode: '100644', type: 'blob', sha: blob.sha })
    done++
    if (done % 200 === 0 || done === files.length) console.log(`  blobs: ${done}/${files.length}`)
  }
}
await Promise.all([...Array(Math.min(CONCURRENCY, files.length))].map((_, i) => blobWorker(i)))

// 2. 递归构建目录树：把 blobs 组织成 路径 → 节点
function buildTreeRecursive(node) {
  return node
}
// node: { type: 'dir', children: Map<name,node> } 或 { type:'blob', item }
const root = { type: 'dir', children: new Map() }
for (const { rel, item } of [...blobByRel.entries()].map(([rel, item]) => ({ rel, item }))) {
  const parts = rel.split('/')
  let cur = root
  for (let i = 0; i < parts.length - 1; i++) {
    if (!cur.children.has(parts[i])) cur.children.set(parts[i], { type: 'dir', children: new Map() })
    cur = cur.children.get(parts[i])
  }
  cur.children.set(parts[parts.length - 1], { type: 'blob', item })
}

// 3. 递归创建 Git 树（每个目录一棵子树）
const treeCache = new Map()
async function createTree(node) {
  if (node.type === 'blob') return node.item
  if (treeCache.has(node)) return treeCache.get(node)
  const entries = []
  for (const [name, child] of node.children.entries()) {
    if (child.type === 'blob') {
      entries.push(child.item)
    } else {
      const subSha = await createTree(child)
      entries.push({ path: name, mode: '040000', type: 'tree', sha: subSha })
    }
  }
  const t = await api('POST', `/repos/${repo}/git/trees`, { tree: entries })
  treeCache.set(node, t.sha)
  return t.sha
}

console.log('创建目录树...')
const rootSha = await createTree(root)
console.log('根目录树:', rootSha.slice(0, 7))

// 4. 提交
const commitPayload = { message: `site update ${new Date().toLocaleString('zh-CN')}`, tree: rootSha }
if (baseSha) commitPayload.parents = [baseSha]
const commit = await api('POST', `/repos/${repo}/git/commits`, commitPayload)
console.log('提交:', commit.sha.slice(0, 7))

// 5. 更新分支引用
try {
  await api('PATCH', `/repos/${repo}/git/refs/heads/${branch}`, { sha: commit.sha, force: true })
} catch {
  await api('POST', `/repos/${repo}/git/refs`, { ref: `refs/heads/${branch}`, sha: commit.sha })
}
console.log(`✅ 已推送 ${files.length} 个文件到 ${repo}@${branch}`)
if (branch === 'main') console.log('已触发 GitHub Actions。')
