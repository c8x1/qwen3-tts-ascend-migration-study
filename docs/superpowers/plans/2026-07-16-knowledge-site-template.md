# Knowledge Site Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一份可离线打开的知识站模板页，实现暖纸张三栏布局、左右栏独立收缩、响应式抽屉、偏好记忆、无脚本降级与自动化视觉和可访问性验收。

**Architecture:** `site/index.html` 保存完整语义内容，`theme.css` 负责视觉令牌，`layout.css` 负责三栏、断点和打印，`app.js` 只负责渐进增强的侧栏状态机。Playwright 从本地 Python 静态服务器验证结构、交互、三类视口、无脚本降级、可访问性和截图；运行时不使用 Node 或任何远程资源。

**Tech Stack:** HTML5、CSS3、原生 ES modules、Node.js 24、npm 11、Playwright 1.61.1、axe-core Playwright 4.12.1、Python 3 静态服务器。

## Global Constraints

- 视觉采用“工程工作台布局 × 技术专著配色”。
- 页面画布 `#f7f1e7`，主文字 `#2b251f`，强调色 `#934735`，代码背景 `#22211e`。
- 宽屏左栏 `240px`、右栏 `245px`；收起后保留约 `40px` 图标轨道。
- `≥1200px` 默认双栏展开；`721–1199px` 默认右栏收起；`≤720px` 默认双抽屉关闭。
- 左右栏独立切换；快捷键分别为 `Alt+[` 与 `Alt+]`。
- 本地存储键固定为 `q3a.sidebar.left` 和 `q3a.sidebar.right`，允许值只有 `expanded` 与 `collapsed`。
- 手机进入时关闭抽屉但不覆盖桌面偏好；返回桌面恢复保存值。
- JavaScript 或 `localStorage` 失败时正文、章节、证据和引用仍可访问。
- 页面不得加载远程字体、CSS、JavaScript 或图片。
- 状态不能只依赖颜色；交互必须满足键盘、焦点和 `aria-expanded` 要求。
- 持续维护 `IMPLEMENTATION_NOTES.md`；小的不确定性采用保守方案并记录偏差，大方向变化才询问用户。
- 每个任务完成后运行对应验证、更新 notes、提交并推送 `agent/knowledge-site-template`；最终审查通过后再合并到 `main`。

---

## File Map

| Path | Responsibility |
| --- | --- |
| `README.md` | 项目入口、模板预览和测试命令 |
| `IMPLEMENTATION_NOTES.md` | 当前进度、重大决策、保守偏差与证据缺口 |
| `package.json` | 固定开发依赖和测试脚本 |
| `playwright.config.js` | 本地服务器、测试目录、截图与 trace 配置 |
| `site/index.html` | 完整语义内容和组件标记 |
| `site/assets/theme.css` | 色彩、字体、标签、代码和基础组件视觉 |
| `site/assets/layout.css` | 三栏、收缩、响应式抽屉、打印与无脚本布局 |
| `site/assets/app.js` | 侧栏偏好、断点、抽屉、快捷键和焦点状态机 |
| `tests/site/template-structure.spec.js` | 语义结构、运行时依赖和视觉令牌检查 |
| `tests/site/sidebar-behavior.spec.js` | 独立收缩、持久化、非法状态与快捷键 |
| `tests/site/responsive-accessibility.spec.js` | 手机抽屉、无脚本、axe、打印和边界内容 |
| `tests/site/template-visual.spec.js` | 三类视口截图基线 |

### Task 1: 建立共享治理和浏览器测试工具链

**Files:**
- Create: `README.md`
- Create: `IMPLEMENTATION_NOTES.md`
- Modify: `.gitignore`
- Create: `package.json`
- Create: `playwright.config.js`
- Create: `tests/site/harness.spec.js`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-07-16-knowledge-site-template-design.md`
- Produces: `npm test`、本地测试服务器、全局 notes 格式和后续任务共享的 Playwright 配置。

- [ ] **Step 1: 写入工具链配置**

Create `package.json`:

```json
{
  "name": "qwen3-tts-ascend-migration-study",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "serve": "python3 -m http.server 4173",
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:update-snapshots": "playwright test --update-snapshots"
  },
  "devDependencies": {
    "@axe-core/playwright": "4.12.1",
    "@playwright/test": "1.61.1"
  }
}
```

Create `playwright.config.js`:

```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/site',
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
  webServer: {
    command: 'python3 -m http.server 4173',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false,
    timeout: 10_000,
  },
});
```

- [ ] **Step 2: 写入工具链冒烟测试**

Create `tests/site/harness.spec.js`:

```javascript
import { expect, test } from '@playwright/test';

test('browser harness runs JavaScript', async ({ page }) => {
  await page.setContent('<main><h1>Harness</h1></main>');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Harness');
});
```

- [ ] **Step 3: 安装固定依赖和 Chromium**

Run:

```bash
npm install
npx playwright install chromium
```

Expected: `package-lock.json` is created; commands exit 0.

- [ ] **Step 4: 运行冒烟测试**

Run:

```bash
npm test -- tests/site/harness.spec.js
```

Expected: 1 test passed.

- [ ] **Step 5: 建立项目入口与 notes**

Create `README.md`:

````markdown
# Qwen3-TTS → Ascend 910B Migration Study

本仓库研究 Qwen3-TTS 训练工程迁移到华为 Ascend 910B 所需的成熟参考项目、训练知识和源码映射。

## Template preview

```bash
npm install
npx playwright install chromium
npm run serve
```

Open `http://127.0.0.1:4173/site/`.

## Tests

```bash
npm test
```

## Scope boundary

The repository studies existing migration projects. It does not claim that Qwen3-TTS training has been ported or validated on Ascend 910B.
````

Create `IMPLEMENTATION_NOTES.md`:

```markdown
# Implementation Notes

## Current status

- Phase: Knowledge-site template
- Active task: Task 1 — shared governance and Playwright harness
- Last verified commit: `09fb855`

## Completed checkpoints

- Research design approved
- Template visual and interaction specification approved

## Major decisions requiring user confirmation

- None. The template direction is approved.

## Conservative deviations

| ID | Date | Stage | Uncertainty | Conservative choice | Reason | Impact | Revisit trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEV-000 | 2026-07-16 | Template setup | No deviation recorded | Preserve approved specification | Initial state | None | New uncertainty discovered |

## Evidence gaps

- Template implementation and automated checks have not run yet.

## Next actions

1. Build the semantic static page and visual system.
2. Implement independent sidebar state.
3. Verify responsive, no-script, accessibility, print, and visual behavior.
```

- [ ] **Step 6: 扩展忽略规则**

Append to `.gitignore`:

```gitignore
node_modules/
playwright-report/
test-results/
.env
.env.*
*.pem
*.key
models/
weights/
datasets/
checkpoints/
```

- [ ] **Step 7: 验证工具链与公开仓库边界**

Run:

```bash
npm test -- tests/site/harness.spec.js
git check-ignore node_modules/example playwright-report/index.html test-results/run.zip .env weights/model.bin datasets/train.json
git diff --check
```

Expected: 1 test passed; every sensitive or generated path is ignored; whitespace check has no output.

- [ ] **Step 8: 更新 notes 并提交推送**

Change `Active task` to Task 2, add the fixed Playwright harness to completed checkpoints, and replace the template-tooling evidence gap with the semantic-page next action.

```bash
git add README.md IMPLEMENTATION_NOTES.md .gitignore package.json package-lock.json playwright.config.js tests/site/harness.spec.js
git commit -m "chore: add knowledge site test harness"
git push -u origin agent/knowledge-site-template
```

Expected: commit and push succeed.

This task also fulfills the shared `README.md`, `.gitignore`, and `IMPLEMENTATION_NOTES.md` governance setup described in Task 1 of the reference-selection plan. When that plan resumes, verify and reuse these files instead of overwriting them.

### Task 2: 构建语义化三栏模板与视觉系统

**Files:**
- Create: `tests/site/template-structure.spec.js`
- Create: `site/index.html`
- Create: `site/assets/theme.css`
- Create: `site/assets/layout.css`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: approved visual tokens and component names.
- Produces: DOM IDs `chapter-nav`, `article-content`, `evidence-rail`; controls `toggle-left`, `toggle-right`; complete content usable without JavaScript.

- [ ] **Step 1: 先写结构和运行时依赖测试**

Create `tests/site/template-structure.spec.js`:

```javascript
import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/site/');
});

test('page exposes semantic regions and one heading level one', async ({ page }) => {
  await expect(page).toHaveTitle(/Qwen3-TTS.*Ascend/);
  await expect(page.getByRole('navigation', { name: '章节导航' })).toBeVisible();
  await expect(page.getByRole('main')).toBeVisible();
  await expect(page.getByRole('complementary', { name: '证据与页内目录' })).toBeVisible();
  await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
});

test('sidebar controls expose fixed contracts', async ({ page }) => {
  const left = page.locator('#toggle-left');
  const right = page.locator('#toggle-right');
  await expect(left).toHaveAttribute('aria-controls', 'chapter-nav');
  await expect(right).toHaveAttribute('aria-controls', 'evidence-rail');
  await expect(left).toHaveAttribute('aria-expanded', 'true');
  await expect(right).toHaveAttribute('aria-expanded', 'true');
});

test('runtime resources are local', async ({ page }) => {
  const resources = await page.evaluate(() =>
    performance.getEntriesByType('resource').map((entry) => entry.name)
  );
  expect(resources.every((url) => url.startsWith(location.origin))).toBe(true);
});

test('approved visual tokens are present', async ({ page }) => {
  const tokens = await page.locator('html').evaluate((node) => {
    const styles = getComputedStyle(node);
    return {
      canvas: styles.getPropertyValue('--canvas').trim(),
      ink: styles.getPropertyValue('--ink').trim(),
      accent: styles.getPropertyValue('--accent').trim(),
      code: styles.getPropertyValue('--code-bg').trim(),
    };
  });
  expect(tokens).toEqual({ canvas: '#f7f1e7', ink: '#2b251f', accent: '#934735', code: '#22211e' });
});
```

- [ ] **Step 2: 运行结构测试并确认页面缺失**

Run:

```bash
npm test -- tests/site/template-structure.spec.js
```

Expected: FAIL because `/site/` does not contain the required semantic regions.

- [ ] **Step 3: 写入完整模板 HTML**

Create `site/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Qwen3-TTS 到 Ascend 910B 训练迁移知识站模板">
  <title>HCCL 并行初始化调用链 · Qwen3-TTS × Ascend 910B</title>
  <link rel="stylesheet" href="assets/theme.css">
  <link rel="stylesheet" href="assets/layout.css">
</head>
<body>
  <header class="site-header">
    <div class="brand">Qwen3-TTS × Ascend <small>Migration Field Notes</small></div>
    <label class="search"><span class="sr-only">搜索</span><input type="search" placeholder="搜索文件、类、配置项、证据编号"></label>
    <div class="revision">主参考项目 · commit 8f21c4a</div>
  </header>

  <div class="site-shell">
    <nav id="chapter-nav" class="chapter-nav" aria-label="章节导航">
      <button id="toggle-left" class="sidebar-toggle left-toggle" type="button" aria-controls="chapter-nav" aria-expanded="true" aria-label="收起章节导航">‹</button>
      <div class="rail-icons" aria-hidden="true"><span>⌂</span><span>▤</span><span>⌘</span><span>↔</span></div>
      <div class="sidebar-content">
        <p class="nav-label">学习路径</p>
        <a href="#">01 · 项目与证据</a><a href="#">02 · Ascend 基础</a>
        <p class="nav-label">源码走读</p>
        <a href="#">03 · 训练入口</a><a class="active" href="#">04 · 分布式初始化</a>
        <a class="sub" href="#call-chain">4.1 设备绑定</a><a class="sub" href="#source">4.2 HCCL 通信域</a><a class="sub" href="#verification">4.3 模型并行状态</a>
        <a href="#">05 · 数据流水线</a><a href="#">06 · 模型与 Loss</a><a href="#">07 · Checkpoint</a>
        <p class="nav-label">迁移映射</p>
        <a href="#">NVIDIA → Ascend</a><a href="#">未来实验清单</a>
      </div>
      <button class="drawer-close" type="button" data-close-drawer="left">关闭章节导航</button>
    </nav>

    <main id="article-content">
      <article>
        <p class="breadcrumb">源码走读 / 分布式初始化 / HCCL</p>
        <h1>HCCL 并行初始化调用链</h1>
        <p class="lead">从训练入口开始，沿着 MindSpeed 注册、设备绑定和通信域建立过程，理解多机训练真正启动前发生了什么。</p>
        <div class="badges"><span class="badge verified">已证实 · S 级</span><span class="badge ascend">Ascend 910B</span><span class="badge pending">性能待真机验证</span></div>

        <section id="call-chain">
          <h2>1. 调用链位置</h2>
          <div class="call-chain" aria-label="初始化调用链"><code>pretrain.py</code><span>→</span><code>initialize_megatron()</code><span>→</span><code>initialize_distributed()</code><span>→</span><code>parallel_state</code></div>
          <p>这一层同时决定当前进程绑定哪张 NPU、默认进程组使用什么后端，以及 TP、PP、CP 通信组如何切分。</p>
        </section>

        <section id="source">
          <h2>2. 关键源码</h2>
          <div class="code-header"><span>mindspeed/training/initialize.py · L142</span><span>复制 · GitHub ↗</span></div>
          <pre><code><span class="kw">def</span> <span class="fn">initialize_distributed</span>(args):
    <span class="cm"># 先绑定本地设备，再创建默认通信域</span>
    torch_npu.npu.set_device(args.local_rank)
    dist.init_process_group(
        backend=<span class="str">"hccl"</span>,
        world_size=args.world_size,
        rank=args.rank,
    )
    parallel_state.initialize_model_parallel(
        tensor_model_parallel_size=args.tensor_parallel_size
    )</code></pre>
        </section>

        <section id="verification">
          <h2>3. 验证方法</h2>
          <p>先检查每个进程的设备绑定和全局 rank，再验证默认 HCCL 进程组以及模型并行通信组的成员关系。</p>
        </section>
      </article>
    </main>

    <aside id="evidence-rail" class="evidence-rail" aria-label="证据与页内目录">
      <button id="toggle-right" class="sidebar-toggle right-toggle" type="button" aria-controls="evidence-rail" aria-expanded="true" aria-label="收起证据栏">›</button>
      <div class="rail-icons" aria-hidden="true"><span>§</span><span>✓</span><span>⚠</span><span>↗</span></div>
      <div class="sidebar-content">
        <section class="rail-card"><h2>本页目录</h2><a href="#call-chain">调用链位置</a><a href="#source">关键源码</a><a href="#verification">验证方法</a></section>
        <section class="rail-card"><h2>证据状态</h2><p>官方源码 · 固定 commit<br>官方 HCCL 文档<br>源码静态核验完成</p></section>
        <section class="rail-card"><h2>迁移提醒</h2><p>NCCL → HCCL 不是唯一变化；设备可见性、环境变量和故障诊断方式也需要单独核验。</p></section>
      </div>
      <button class="drawer-close" type="button" data-close-drawer="right">关闭证据栏</button>
    </aside>
  </div>
  <div class="drawer-backdrop" hidden></div>
</body>
</html>
```

- [ ] **Step 4: 写入视觉令牌与组件样式**

Create `site/assets/theme.css`:

```css
:root {
  --canvas: #f7f1e7;
  --header: #e8ddcd;
  --left-bg: #eee5d8;
  --article-bg: #fcf9f3;
  --right-bg: #f1e8dc;
  --ink: #2b251f;
  --muted: #675a4d;
  --accent: #934735;
  --gold: #9b6c29;
  --border: #cdbda7;
  --code-bg: #22211e;
  --code-ink: #f3eee4;
  color-scheme: light;
  font-family: ui-sans-serif, system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  color: var(--ink);
  background: var(--canvas);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--canvas); color: var(--ink); }
button, input { font: inherit; }
button:focus-visible, a:focus-visible, input:focus-visible { outline: 3px solid #1f6f8b; outline-offset: 2px; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
.brand { font-family: ui-serif, "Songti SC", Georgia, serif; font-size: 1rem; font-weight: 700; }
.brand small { display: block; margin-top: .15rem; color: var(--accent); font-family: ui-sans-serif, system-ui, sans-serif; font-size: .58rem; letter-spacing: .14em; text-transform: uppercase; }
.search input { width: min(32rem, 100%); padding: .65rem .85rem; border: 1px solid #bfae97; border-radius: .55rem; color: var(--ink); background: #f8f3eb; }
.revision, .breadcrumb { color: var(--muted); font-size: .75rem; }
h1, h2 { font-family: ui-serif, "Songti SC", Georgia, serif; color: #29221c; }
h1 { margin: .65rem 0 .75rem; font-size: clamp(1.5rem, 3vw, 1.9rem); line-height: 1.2; }
h2 { margin: 0 0 .65rem; font-size: 1.2rem; }
p { line-height: 1.7; }
.lead { max-width: 48rem; margin-bottom: 1.2rem; color: var(--muted); font-family: ui-serif, "Songti SC", Georgia, serif; font-size: 1rem; }
.badge { display: inline-block; margin: 0 .35rem .4rem 0; padding: .28rem .55rem; border: 1px solid; border-radius: 999px; font-size: .72rem; font-weight: 700; }
.verified { color: #315b42; background: #dfeade; border-color: #a9c3ad; }
.ascend { color: #713a2e; background: #f0dcd4; border-color: #d7ab9f; }
.pending { color: #6b511d; background: #f4e8c6; border-color: #d9c17c; }
article section { margin-top: 1.6rem; padding-top: 1.3rem; border-top: 1px solid #ddd0bf; }
.call-chain { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; margin: .8rem 0; }
.call-chain code { padding: .5rem .65rem; border: 1px solid #ccbba4; border-radius: .45rem; color: #54483d; background: #f1e7d9; }
.call-chain span { color: var(--accent); font-weight: 800; }
.code-header { display: flex; justify-content: space-between; gap: 1rem; padding: .55rem .8rem; border-bottom: 1px solid #4b4740; border-radius: .55rem .55rem 0 0; color: #b6aa97; background: #302e29; font-size: .72rem; }
pre { margin: 0; padding: 1rem; overflow-x: auto; border-radius: 0 0 .55rem .55rem; color: var(--code-ink); background: var(--code-bg); font: .8rem/1.65 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.kw { color: #ef8f78; } .fn { color: #e6c982; } .str { color: #a9d38b; } .cm { color: #9da79f; }
.nav-label { margin: 1rem .55rem .4rem; color: var(--gold); font-size: .65rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.chapter-nav a { display: block; margin: .12rem 0; padding: .55rem .65rem; border-radius: .45rem; color: #67594a; font-size: .82rem; text-decoration: none; }
.chapter-nav a.active { color: #fffaf2; background: var(--accent); }
.chapter-nav a.sub { padding-left: 1.35rem; font-size: .76rem; }
.rail-card { margin-bottom: .75rem; padding: .85rem; border: 1px solid #cfbfa9; border-radius: .55rem; background: #faf6ef; }
.rail-card h2 { font-size: .9rem; }
.rail-card p, .rail-card a { display: block; margin: .2rem 0; color: #665747; font-size: .75rem; line-height: 1.6; }
.sidebar-toggle, .drawer-close { border: 1px solid #bba88f; border-radius: .4rem; color: #6d5948; background: #f9f4ec; cursor: pointer; }
.sidebar-toggle { position: absolute; top: .75rem; width: 1.8rem; height: 1.8rem; }
.left-toggle { right: .65rem; } .right-toggle { left: .65rem; }
.rail-icons { display: none; flex-direction: column; align-items: center; gap: 1rem; padding-top: 3.2rem; color: #704335; }
.drawer-close { display: none; width: 100%; margin-top: 1rem; padding: .65rem; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; } }
```

- [ ] **Step 5: 写入三栏、断点和打印样式**

Create `site/assets/layout.css`:

```css
.site-header { position: sticky; top: 0; z-index: 20; display: grid; grid-template-columns: 15rem minmax(18rem, 1fr) 15rem; align-items: center; min-height: 3.65rem; padding: .45rem 1.1rem; border-bottom: 1px solid #c5b59e; background: var(--header); }
.search { justify-self: center; width: min(32rem, 90%); }
.revision { justify-self: end; }
.site-shell { display: grid; grid-template-columns: 15rem minmax(0, 1fr) 15.3125rem; max-width: 107.5rem; min-height: calc(100vh - 3.65rem); margin: 0 auto; }
.chapter-nav, .evidence-rail { position: sticky; top: 3.65rem; align-self: start; height: calc(100vh - 3.65rem); overflow-y: auto; }
.chapter-nav { position: sticky; padding: 1.4rem .85rem; border-right: 1px solid var(--border); background: var(--left-bg); }
.evidence-rail { position: sticky; padding: 1.5rem 1rem; border-left: 1px solid var(--border); background: var(--right-bg); }
main { min-width: 0; background: var(--article-bg); }
article { max-width: 57.5rem; margin: 0 auto; padding: 2.2rem 2.75rem 3rem; }
.drawer-backdrop { display: none; }

html[data-left-sidebar="collapsed"] .site-shell { grid-template-columns: 2.5rem minmax(0, 1fr) 15.3125rem; }
html[data-left-sidebar="collapsed"] .chapter-nav { padding-inline: 0; overflow: hidden; }
html[data-left-sidebar="collapsed"] .chapter-nav .sidebar-content { display: none; }
html[data-left-sidebar="collapsed"] .chapter-nav .rail-icons { display: flex; }
html[data-left-sidebar="collapsed"] .left-toggle { right: .35rem; }
html[data-left-sidebar="collapsed"] .left-toggle { transform: rotate(180deg); }

html[data-right-sidebar="collapsed"] .site-shell { grid-template-columns: 15rem minmax(0, 1fr) 2.5rem; }
html[data-right-sidebar="collapsed"] .evidence-rail { padding-inline: 0; overflow: hidden; }
html[data-right-sidebar="collapsed"] .evidence-rail .sidebar-content { display: none; }
html[data-right-sidebar="collapsed"] .evidence-rail .rail-icons { display: flex; }
html[data-right-sidebar="collapsed"] .right-toggle { left: .35rem; transform: rotate(180deg); }

html[data-left-sidebar="collapsed"][data-right-sidebar="collapsed"] .site-shell { grid-template-columns: 2.5rem minmax(0, 1fr) 2.5rem; }

@media (max-width: 1199px) {
  .site-header { grid-template-columns: 13rem minmax(14rem, 1fr) 6rem; }
  .site-shell { grid-template-columns: 13rem minmax(0, 1fr) 2.5rem; }
  html[data-right-sidebar="expanded"] .site-shell { grid-template-columns: 13rem minmax(0, 1fr) 15.3125rem; }
  html[data-left-sidebar="collapsed"] .site-shell { grid-template-columns: 2.5rem minmax(0, 1fr) 2.5rem; }
  html[data-left-sidebar="collapsed"][data-right-sidebar="expanded"] .site-shell { grid-template-columns: 2.5rem minmax(0, 1fr) 15.3125rem; }
  article { padding-inline: 2rem; }
}

@media (max-width: 720px) {
  .site-header { grid-template-columns: 1fr auto; min-height: 3.25rem; padding-inline: .85rem; }
  .search { display: none; }
  .revision { font-size: 0; }
  .revision::after { content: "⌕"; font-size: 1.1rem; }
  .site-shell { display: block; min-height: 0; }
  main { min-height: calc(100vh - 3.25rem); }
  article { padding: 1.5rem 1.1rem 2.5rem; }
  .chapter-nav, .evidence-rail { position: static; width: auto; height: auto; padding: 1rem; border: 0; }
  .sidebar-toggle { position: fixed; z-index: 35; top: .7rem; }
  .left-toggle { right: 3.2rem; } .right-toggle { right: .8rem; left: auto; }
  .call-chain { align-items: flex-start; flex-direction: column; }
  .call-chain span { margin-left: 1rem; transform: rotate(90deg); }
  pre { font-size: .72rem; }
  html.js .chapter-nav, html.js .evidence-rail { position: fixed; z-index: 40; top: 0; bottom: 0; width: min(20rem, 86vw); height: 100vh; overflow-y: auto; transition: transform .2s ease; }
  html.js .chapter-nav { left: 0; transform: translateX(-105%); border-right: 1px solid var(--border); }
  html.js .evidence-rail { right: 0; transform: translateX(105%); border-left: 1px solid var(--border); }
  html.js[data-drawer-open="left"] .chapter-nav, html.js[data-drawer-open="right"] .evidence-rail { transform: translateX(0); }
  html.js .chapter-nav .sidebar-content, html.js .evidence-rail .sidebar-content { display: block; }
  html.js .chapter-nav .rail-icons, html.js .evidence-rail .rail-icons { display: none; }
  html.js .drawer-close { display: block; }
  html.js .drawer-backdrop { position: fixed; z-index: 30; inset: 0; display: block; background: rgb(43 37 31 / 55%); }
  html.js .drawer-backdrop[hidden] { display: none; }
}

@media print {
  .site-header, .chapter-nav, .sidebar-toggle, .drawer-close, .drawer-backdrop { display: none !important; }
  .site-shell { display: block; }
  main, article { max-width: none; padding: 0; background: white; }
  .evidence-rail { position: static; display: block; width: auto; height: auto; margin-top: 2rem; padding: 1rem 0; border: 0; border-top: 1px solid #888; background: white; }
  .evidence-rail .sidebar-content { display: block !important; }
  .evidence-rail .rail-icons { display: none !important; }
  pre { white-space: pre-wrap; }
}
```

- [ ] **Step 6: 运行结构测试并确认通过**

Run:

```bash
npm test -- tests/site/template-structure.spec.js
```

Expected: 4 tests passed.

- [ ] **Step 7: 更新 notes 并提交推送**

Record semantic page and visual system as completed; set Active task to Task 3. If a browser renders a system-font fallback differently, record it as a conservative deviation and retain system fonts rather than adding a remote dependency.

```bash
git add IMPLEMENTATION_NOTES.md site/index.html site/assets/theme.css site/assets/layout.css tests/site/template-structure.spec.js
git commit -m "feat: add semantic knowledge site template"
git push origin agent/knowledge-site-template
```

Expected: commit and push succeed.

### Task 3: 实现左右栏状态机与持久化

**Files:**
- Create: `tests/site/sidebar-behavior.spec.js`
- Create: `site/assets/app.js`
- Modify: `site/index.html`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: IDs `toggle-left`, `toggle-right`, `chapter-nav`, `evidence-rail`; storage keys from the specification.
- Produces: root attributes `data-left-sidebar`, `data-right-sidebar`, `data-drawer-open`; exported `SidebarController` class.

- [ ] **Step 1: 写入桌面、笔记本和存储行为测试**

Create `tests/site/sidebar-behavior.spec.js`:

```javascript
import { expect, test } from '@playwright/test';

test('wide desktop toggles each sidebar independently', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'expanded');
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'expanded');
  await page.locator('#toggle-left').click();
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'collapsed');
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'expanded');
  await page.locator('#toggle-right').click();
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'collapsed');
});

test('laptop defaults right collapsed and persists valid preferences', async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto('/site/');
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'expanded');
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'collapsed');
  await page.locator('#toggle-left').click();
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'collapsed');
});

test('invalid preferences recover to viewport defaults', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.evaluate(() => {
    localStorage.setItem('q3a.sidebar.left', 'broken');
    localStorage.setItem('q3a.sidebar.right', 'broken');
  });
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'expanded');
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'expanded');
});

test('keyboard shortcuts toggle and aria-expanded follows state', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.keyboard.press('Alt+[');
  await expect(page.locator('#toggle-left')).toHaveAttribute('aria-expanded', 'false');
  await page.keyboard.press('Alt+]');
  await expect(page.locator('#toggle-right')).toHaveAttribute('aria-expanded', 'false');
});

test('storage failure keeps in-memory interaction usable', async ({ page }) => {
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => { throw new Error('storage disabled'); };
    Storage.prototype.setItem = () => { throw new Error('storage disabled'); };
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.locator('#toggle-left').click();
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'collapsed');
});
```

- [ ] **Step 2: 运行行为测试并确认脚本缺失**

Run:

```bash
npm test -- tests/site/sidebar-behavior.spec.js
```

Expected: FAIL because root state attributes do not exist and buttons do not change state.

- [ ] **Step 3: 实现侧栏状态机**

Create `site/assets/app.js`:

```javascript
const VALID = new Set(['expanded', 'collapsed']);
const STORAGE_KEYS = {
  left: 'q3a.sidebar.left',
  right: 'q3a.sidebar.right',
};

export class SidebarController {
  constructor(documentRef = document, windowRef = window) {
    this.document = documentRef;
    this.window = windowRef;
    this.root = documentRef.documentElement;
    this.toggles = {
      left: documentRef.querySelector('#toggle-left'),
      right: documentRef.querySelector('#toggle-right'),
    };
    this.sidebars = {
      left: documentRef.querySelector('#chapter-nav'),
      right: documentRef.querySelector('#evidence-rail'),
    };
    this.backdrop = documentRef.querySelector('.drawer-backdrop');
    this.lastTrigger = null;
    this.memory = new Map();
    this.boundKeydown = (event) => this.onKeydown(event);
    this.boundResize = () => this.onResize();
  }

  mode() {
    if (this.window.innerWidth <= 720) return 'mobile';
    if (this.window.innerWidth < 1200) return 'laptop';
    return 'wide';
  }

  defaultState(side) {
    return this.mode() === 'laptop' && side === 'right' ? 'collapsed' : 'expanded';
  }

  read(side) {
    try {
      const value = this.window.localStorage.getItem(STORAGE_KEYS[side]);
      if (VALID.has(value)) return value;
      if (value !== null) this.window.localStorage.removeItem(STORAGE_KEYS[side]);
    } catch {
      const value = this.memory.get(side);
      if (VALID.has(value)) return value;
    }
    return this.defaultState(side);
  }

  write(side, value) {
    this.memory.set(side, value);
    try {
      this.window.localStorage.setItem(STORAGE_KEYS[side], value);
    } catch {
      // In-memory state remains available for this page view.
    }
  }

  apply(side, value) {
    this.root.dataset[`${side}Sidebar`] = value;
    const expanded = value === 'expanded';
    this.toggles[side].setAttribute('aria-expanded', String(expanded));
    this.toggles[side].setAttribute('aria-label', `${expanded ? '收起' : '展开'}${side === 'left' ? '章节导航' : '证据栏'}`);
  }

  toggle(side) {
    if (this.mode() === 'mobile') {
      this.openDrawer(side, this.toggles[side]);
      return;
    }
    const current = this.root.dataset[`${side}Sidebar`];
    const next = current === 'expanded' ? 'collapsed' : 'expanded';
    this.write(side, next);
    this.apply(side, next);
  }

  openDrawer(side, trigger) {
    this.closeDrawer(false);
    this.lastTrigger = trigger;
    this.root.dataset.drawerOpen = side;
    this.backdrop.hidden = false;
    this.sidebars.left.inert = side !== 'left';
    this.sidebars.right.inert = side !== 'right';
    this.sidebars[side].setAttribute('role', 'dialog');
    this.sidebars[side].setAttribute('aria-modal', 'true');
    this.toggles[side].setAttribute('aria-expanded', 'true');
    const target = this.sidebars[side].querySelector('a, button, input, [tabindex]:not([tabindex="-1"])');
    target?.focus();
  }

  closeDrawer(restoreFocus = true) {
    const side = this.root.dataset.drawerOpen;
    if (!side) {
      this.backdrop.hidden = true;
      return;
    }
    delete this.root.dataset.drawerOpen;
    this.backdrop.hidden = true;
    this.sidebars[side].removeAttribute('role');
    this.sidebars[side].removeAttribute('aria-modal');
    if (this.mode() === 'mobile') {
      this.sidebars.left.inert = true;
      this.sidebars.right.inert = true;
    }
    this.toggles[side].setAttribute('aria-expanded', 'false');
    if (restoreFocus) this.lastTrigger?.focus();
  }

  trapFocus(event) {
    const side = this.root.dataset.drawerOpen;
    if (!side || event.key !== 'Tab') return;
    const focusable = [...this.sidebars[side].querySelectorAll('a, button, input, [tabindex]:not([tabindex="-1"])')]
      .filter((node) => !node.disabled && node.getClientRects().length > 0);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && this.document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && this.document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  onKeydown(event) {
    if (event.key === 'Escape') this.closeDrawer();
    if (event.altKey && event.key === '[') { event.preventDefault(); this.toggle('left'); }
    if (event.altKey && event.key === ']') { event.preventDefault(); this.toggle('right'); }
    this.trapFocus(event);
  }

  onResize() {
    if (this.mode() === 'mobile') {
      this.closeDrawer(false);
      this.sidebars.left.inert = true;
      this.sidebars.right.inert = true;
      this.toggles.left.setAttribute('aria-expanded', 'false');
      this.toggles.right.setAttribute('aria-expanded', 'false');
      return;
    }
    this.closeDrawer(false);
    this.sidebars.left.inert = false;
    this.sidebars.right.inert = false;
    this.sidebars.left.removeAttribute('role');
    this.sidebars.right.removeAttribute('role');
    this.sidebars.left.removeAttribute('aria-modal');
    this.sidebars.right.removeAttribute('aria-modal');
    this.apply('left', this.read('left'));
    this.apply('right', this.read('right'));
  }

  init() {
    this.root.classList.add('js');
    this.apply('left', this.read('left'));
    this.apply('right', this.read('right'));
    if (this.mode() === 'mobile') this.onResize();
    this.toggles.left.addEventListener('click', () => this.toggle('left'));
    this.toggles.right.addEventListener('click', () => this.toggle('right'));
    this.backdrop.addEventListener('click', () => this.closeDrawer());
    this.document.querySelectorAll('[data-close-drawer]').forEach((button) =>
      button.addEventListener('click', () => this.closeDrawer())
    );
    this.document.addEventListener('keydown', this.boundKeydown);
    this.window.addEventListener('resize', this.boundResize);
  }
}

new SidebarController().init();
```

- [ ] **Step 4: 从模板加载 ES module**

Add immediately before `</body>` in `site/index.html`:

```html
  <script type="module" src="assets/app.js"></script>
```

- [ ] **Step 5: 运行结构与侧栏测试**

Run:

```bash
npm test -- tests/site/template-structure.spec.js tests/site/sidebar-behavior.spec.js
```

Expected: 9 tests passed.

- [ ] **Step 6: 更新 notes 并提交推送**

Record independent sidebars, persistence, invalid-state recovery and shortcuts as completed. Record any browser-specific shortcut conflict as a deviation; preserve accessible buttons as the canonical interaction.

```bash
git add IMPLEMENTATION_NOTES.md site/index.html site/assets/app.js tests/site/sidebar-behavior.spec.js
git commit -m "feat: add collapsible sidebar state"
git push origin agent/knowledge-site-template
```

Expected: commit and push succeed.

### Task 4: 验证手机抽屉、降级、可访问性、打印与视觉基线

**Files:**
- Create: `tests/site/responsive-accessibility.spec.js`
- Create: `tests/site/template-visual.spec.js`
- Create: `tests/site/template-visual.spec.js-snapshots/desktop-template-chromium-darwin.png`
- Create: `tests/site/template-visual.spec.js-snapshots/laptop-template-chromium-darwin.png`
- Create: `tests/site/template-visual.spec.js-snapshots/mobile-template-chromium-darwin.png`
- Modify: `README.md`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: complete template and `SidebarController`.
- Produces: responsive behavior proof, axe audit, no-script and print proof, tracked visual baselines.

- [ ] **Step 1: 写入响应式、无脚本与可访问性测试**

Create `tests/site/responsive-accessibility.spec.js`:

```javascript
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('mobile starts closed, opens a drawer, traps focus, and Escape restores focus', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/');
  await expect(page.locator('html')).not.toHaveAttribute('data-drawer-open', /.+/);
  await page.locator('#toggle-left').click();
  await expect(page.locator('html')).toHaveAttribute('data-drawer-open', 'left');
  await expect(page.locator('#chapter-nav')).toHaveAttribute('role', 'dialog');
  await expect(page.locator('#chapter-nav')).toHaveAttribute('aria-modal', 'true');
  await expect(page.locator('#evidence-rail')).toHaveAttribute('inert', '');
  await page.locator('[data-close-drawer="left"]').focus();
  await page.keyboard.press('Tab');
  await expect(page.locator('#chapter-nav a').first()).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.locator('html')).not.toHaveAttribute('data-drawer-open', /.+/);
  await expect(page.locator('#chapter-nav')).toHaveAttribute('inert', '');
  await expect(page.locator('#toggle-left')).toBeFocused();
});

test('mobile never auto-opens a saved desktop preference', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.evaluate(() => localStorage.setItem('q3a.sidebar.right', 'expanded'));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.locator('html')).not.toHaveAttribute('data-drawer-open', /.+/);
  await expect(page.locator('#toggle-right')).toHaveAttribute('aria-expanded', 'false');
  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'expanded');
});

test('all content remains visible without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4173/site/');
  await expect(page.getByRole('navigation', { name: '章节导航' })).toBeVisible();
  await expect(page.getByRole('main')).toBeVisible();
  await expect(page.getByRole('complementary', { name: '证据与页内目录' })).toBeVisible();
  await context.close();
});

test('template has no serious accessibility violations', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter((item) => ['serious', 'critical'].includes(item.impact));
  expect(serious).toEqual([]);
});

test('print hides navigation and keeps evidence', async ({ page }) => {
  await page.goto('/site/');
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('.site-header')).toBeHidden();
  await expect(page.locator('#chapter-nav')).toBeHidden();
  await expect(page.locator('#article-content')).toBeVisible();
  await expect(page.locator('#evidence-rail')).toBeVisible();
});

test('long title and code do not widen the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/');
  await page.locator('h1').evaluate((node) => { node.textContent = '超长训练配置与多机多卡分布式初始化调用链'.repeat(5); });
  await page.locator('pre code').evaluate((node) => { node.textContent += `\n${'very_long_symbol_'.repeat(30)}`; });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
});
```

- [ ] **Step 2: 写入三视口视觉测试**

Create `tests/site/template-visual.spec.js`:

```javascript
import { expect, test } from '@playwright/test';

for (const [name, viewport] of Object.entries({
  desktop: { width: 1440, height: 900 },
  laptop: { width: 1024, height: 768 },
  mobile: { width: 390, height: 844 },
})) {
  test(`${name} template matches approved baseline`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto('/site/');
    await expect(page).toHaveScreenshot(`${name}-template.png`, {
      fullPage: true,
      animations: 'disabled',
      maxDiffPixelRatio: 0.01,
    });
  });
}
```

- [ ] **Step 3: 运行功能和可访问性测试**

Run:

```bash
npm test -- tests/site/responsive-accessibility.spec.js
```

Expected: 6 tests passed. If axe finds a serious or critical violation, fix the exact DOM or color issue and rerun before proceeding.

- [ ] **Step 4: 生成并复验截图基线**

Run:

```bash
npm run test:update-snapshots -- tests/site/template-visual.spec.js
npm test -- tests/site/template-visual.spec.js
```

Expected: 3 snapshots generated; second command reports 3 tests passed with no diff.

- [ ] **Step 5: 运行完整测试和公开内容审计**

Run:

```bash
npm test
git diff --check
git status --short
git ls-files | rg '(^|/)(\.env|models|weights|datasets|checkpoints)/|\.(pem|key)$' && exit 1 || true
```

Expected: 19 tests passed; whitespace check is clean; only intended template, tests, notes, README, package and snapshot files are changed; restricted-path audit finds nothing.

- [ ] **Step 6: 完成 README 与 notes**

Add to `README.md`:

```markdown
## Template behavior

- Desktop: both sidebars expanded by default
- Laptop: evidence sidebar collapsed by default
- Mobile: both sidebars open as drawers
- Shortcuts: `Alt+[` and `Alt+]`
- Runtime: local static HTML/CSS/JavaScript only
```

Update `IMPLEMENTATION_NOTES.md`: mark all four template tasks complete, list the exact full-test result, move remaining issues to Evidence gaps, preserve every conservative deviation, and set Next actions to Phase 1 reference-project research.

- [ ] **Step 7: 提交并推送验收产物**

```bash
git add README.md IMPLEMENTATION_NOTES.md tests/site site
git commit -m "test: verify responsive knowledge site template"
git push origin agent/knowledge-site-template
```

Expected: commit and push succeed.

## Completion Verification

Immediately before claiming the template complete, run:

```bash
npm test
git diff --check
git status -sb
git rev-parse HEAD
git ls-remote origin refs/heads/agent/knowledge-site-template
```

Required evidence:

- 19 Playwright tests pass.
- Desktop, laptop and mobile screenshots match tracked baselines.
- Local `agent/knowledge-site-template` is clean and equals its remote branch.
- No remote runtime resources, secrets, model weights, datasets or checkpoints are tracked.
- `IMPLEMENTATION_NOTES.md` contains completed checkpoints, deviations, evidence gaps and next actions.
