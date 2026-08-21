#!/usr/bin/env node
/**
 * X-markdown 一键同步到手机端（GitHub Pages）
 * ===========================================
 * 流程: 导出数据到 public/data → 提交并推送 main → GitHub Actions 自动构建并部署。
 *
 * 用法:
 *   node scripts/sync.mjs [--repo owner/repo] [--push] [--message "msg"]
 *
 * 依赖:
 *   - Python 3 (含 sqlite3)
 *   - Node.js + npm
 *   - git + 已配置远程 origin（或用 --repo 指定）
 *
 * 说明:
 *   - 部署采用 GitHub Actions（.github/workflows/deploy.yml），构建产物由 CI 完成，
 *     无需本地构建 dist。
 *   - 首次部署需要在 GitHub 仓库开启 Actions 工作流权限（通常默认开启）。
 */
import { execSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const DATA_DIR = path.join(ROOT, 'xmarkdown-mobile', 'public', 'data')

const args = process.argv.slice(2)
function argVal(name) {
  const i = args.findIndex((a) => a === `--${name}`)
  return i >= 0 ? args[i + 1] : null
}
const repo = argVal('repo')
const message = argVal('message') || `site update ${new Date().toLocaleString('zh-CN')}`
const doPush = args.includes('--push')

function run(cmd, cwd = ROOT) {
  console.log(`> ${cmd}`)
  execSync(cmd, { cwd, stdio: 'inherit', shell: process.platform === 'win32' ? 'cmd.exe' : '/bin/bash' })
}
function step(msg) {
  console.log('\n' + '='.repeat(60))
  console.log('  ' + msg)
  console.log('='.repeat(60))
}

// ---------- 1. 导出数据 ----------
step('步骤 1/3：从桌面端数据库导出数据')
const py = process.platform === 'win32' ? 'python' : 'python3'
run(`"${py}" tools/export_site.py`, ROOT)

// ---------- 2. git add / commit / push ----------
step('步骤 2/3：提交导出数据')
// 确保在 main 分支（或当前分支）
run('git add xmarkdown-mobile/public/data', ROOT)
try {
  run(`git commit -m "${message.replace(/"/g, "'")}"`, ROOT)
} catch {
  console.log('（没有新的改动可提交，继续）')
}

// 若指定了 repo 且无 origin，则添加远程
if (repo && !doPush) {
  try {
    run(`git remote remove origin`, ROOT)
  } catch { /* ignore */ }
  const url = repo.includes('/') ? `https://github.com/${repo}.git` : repo
  run(`git remote add origin ${url}`, ROOT)
}

if (doPush) {
  step('步骤 3/3：推送并触发 GitHub Actions 部署')
  // 确定推送分支
  let branch = 'main'
  try {
    branch = execSync('git rev-parse --abbrev-ref HEAD', { cwd: ROOT, encoding: 'utf8' }).trim() || 'main'
  } catch { /* ignore */ }
  try {
    run('git push -u origin HEAD', ROOT)
  } catch (e) {
    // 尝试显式分支
    try {
      run(`git push -u origin ${branch}`, ROOT)
    } catch {
      console.error('推送失败，请检查远程仓库与登录状态。')
      process.exit(1)
    }
  }
  console.log(`\n已推送到 ${branch}。GitHub Actions 正在构建并部署，通常 1-3 分钟。`)
  console.log(`访问: https://<用户名>.github.io/<仓库名>/`)
} else {
  console.log('\n数据已导出并提交。加 --push 参数即可推送到 GitHub 触发部署。')
  console.log('示例: node scripts/sync.mjs --repo owner/repo --push')
}
