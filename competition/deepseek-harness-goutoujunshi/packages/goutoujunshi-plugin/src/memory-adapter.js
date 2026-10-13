import { spawn } from 'node:child_process'
import { resolve } from 'node:path'

const ALLOWED_ACTIONS = new Set(['status', 'show', 'context', 'enable', 'pause', 'resume', 'apply', 'undo'])

// Windows 上 `python3` 常常是 Microsoft Store 的应用执行别名存根：它不接受参数、返回 0 字节输出、
// 退出码 9009，spawn 本身也不会报错。因此不能只判断「进程是否启动」，必须逐个候选解释器试跑并
// 检查它是否真的返回了本脚本的 JSON 结构，否则长期记忆会在 Windows 上静默失效。
const PYTHON_CANDIDATES = [
  { command: 'python3', prefixArgs: [] },
  { command: 'python', prefixArgs: [] },
  { command: 'py', prefixArgs: ['-3'] },
]

const RESULT_KEYS = ['ok', 'error', 'consent_enabled', 'exists', 'memory_count', 'memories', 'undone_op_id']

function looksLikeStoreAlias(parsed, stderr) {
  const keys = parsed && typeof parsed === 'object' ? Object.keys(parsed) : []
  // 解析成功但一个脚本字段都没有（例如空对象）说明这个解释器只是替身，不是 memory_store.py。
  if (!keys.some(key => RESULT_KEYS.includes(key))) return true
  if (!stderr.trim()) return false
  return Boolean(parsed?.error) || /python was not found|应用商店|App execution alias|无法启动/i.test(stderr)
}

function runCandidate(candidate, args, cwd, env, stdin) {
  return new Promise((accept, reject) => {
    const child = spawn(candidate.command, [...candidate.prefixArgs, ...args], {
      cwd,
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    let stdout = ''
    let stderr = ''
    child.stdout.setEncoding('utf8')
    child.stderr.setEncoding('utf8')
    child.stdout.on('data', chunk => { stdout += chunk })
    child.stderr.on('data', chunk => { stderr += chunk })
    child.once('error', error => reject(error))
    child.once('close', code => {
      let parsed
      try {
        parsed = JSON.parse(stdout || '{}')
      } catch {
        accept({ storeAlias: true, detail: (stderr || stdout).trim() })
        return
      }
      if (looksLikeStoreAlias(parsed, stderr)) {
        accept({ storeAlias: true, detail: (stderr || stdout).trim() })
        return
      }
      accept({ storeAlias: false, parsed, code, stderr })
    })
    child.stdin.end(stdin)
  })
}

export async function callReadonlyMemoryStore({ skillRoot, memoryDirectory, action, payload = {}, confirmed = false }) {
  if (!ALLOWED_ACTIONS.has(action)) throw new Error(`不支持的记忆动作：${action}`)
  const script = resolve(skillRoot, 'scripts/memory_store.py')
  const args = [script, action]
  let stdin = ''
  if (['show', 'context'].includes(action) && payload.subjectId) args.push('--subject-id', payload.subjectId)
  if (action === 'context' && payload.maxChars) args.push('--max-chars', String(payload.maxChars))
  if (action === 'enable' && confirmed) args.push('--confirm')
  if (action === 'undo' && payload.operationId) args.push('--op-id', payload.operationId)
  if (action === 'apply') stdin = JSON.stringify(payload.delta || payload)

  const cwd = skillRoot
  const env = { ...process.env, GOUTOUJUNSHI_MEMORY_DIR: resolve(memoryDirectory) }
  let lastFailure = ''
  for (const candidate of PYTHON_CANDIDATES) {
    let outcome
    try {
      outcome = await runCandidate(candidate, args, cwd, env, stdin)
    } catch (error) {
      lastFailure = `${candidate.command}: ${error.message}`
      continue
    }
    if (outcome.storeAlias) {
      lastFailure = `${candidate.command}: ${outcome.detail || '未返回记忆脚本的 JSON 结果'}`
      continue
    }
    if (outcome.code !== 0) {
      throw new Error(outcome.parsed?.error?.message || outcome.stderr || `记忆脚本退出码 ${outcome.code}`)
    }
    return outcome.parsed
  }
  throw new Error(`找不到可用的 Python 解释器：${lastFailure || 'python3 / python / py -3 均不可用'}`)
}
