import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const SOURCE_COMMIT = '022e286b98fbec7e1e916cb940cdf532cd9f488e';

async function expectWcagAA(page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
}

async function paintedArea(locator) {
  return locator.evaluate((node) => {
    let rect = node.getBoundingClientRect();
    let left = Math.max(0, rect.left);
    let top = Math.max(0, rect.top);
    let right = Math.min(innerWidth, rect.right);
    let bottom = Math.min(innerHeight, rect.bottom);
    for (let parent = node.parentElement; parent; parent = parent.parentElement) {
      const style = getComputedStyle(parent);
      const clipsX = /(auto|scroll|hidden|clip)/.test(style.overflowX);
      const clipsY = /(auto|scroll|hidden|clip)/.test(style.overflowY);
      if (!clipsX && !clipsY) continue;
      rect = parent.getBoundingClientRect();
      if (clipsX) { left = Math.max(left, rect.left); right = Math.min(right, rect.right); }
      if (clipsY) { top = Math.max(top, rect.top); bottom = Math.min(bottom, rect.bottom); }
    }
    return Math.max(0, right - left) * Math.max(0, bottom - top);
  });
}

async function topPaintedPoints(link) {
  return link.locator('.rail-tooltip').evaluate((tooltip) => {
    const rect = tooltip.getBoundingClientRect();
    const points = [
      [rect.left + rect.width / 2, rect.top + rect.height / 2],
      [rect.left + Math.min(8, rect.width / 4), rect.top + rect.height / 2],
      [rect.right - Math.min(8, rect.width / 4), rect.top + rect.height / 2],
    ];
    return points.map(([x, y]) => {
      const stack = document.elementsFromPoint(x, y);
      const top = document.elementFromPoint(x, y);
      return {
        x,
        y,
        topTag: top?.tagName ?? null,
        topClass: top?.className ?? null,
        painted: Boolean(top && (top === tooltip || tooltip.contains(top) || tooltip.parentElement.contains(top))),
        stack: stack.slice(0, 4).map((node) => `${node.tagName}.${node.className}`),
      };
    });
  });
}

test('collapsed rails paint every named keyboard destination and tooltip inside the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.locator('#toggle-left').click();
  await page.locator('#toggle-right').click();

  for (const name of ['首页', '章节', '目录']) {
    const link = page.getByRole('link', { name, exact: true });
    await expect(link).toBeVisible();
    for (const interaction of ['hover', 'focus']) {
      if (interaction === 'hover') await link.hover();
      else await link.focus();
      if (interaction === 'focus') await expect(link).toBeFocused();
      expect(await paintedArea(link.locator('.rail-tooltip')), `${name} ${interaction} tooltip is actually painted`).toBeGreaterThan(0);
      const points = await topPaintedPoints(link);
      expect(points, `${name} ${interaction} tooltip hit-test: ${JSON.stringify(points)}`)
        .toEqual(points.map((point) => expect.objectContaining({ painted: true })));
    }
  }
});

test('mobile header preserves the chapter title and opens a real search input', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/');

  await expect(page.locator('.mobile-chapter-title')).toContainText('Qwen3-TTS 官方目标源码学习路径');
  const searchButton = page.getByRole('button', { name: '打开站内搜索' });
  await searchButton.focus();
  await page.keyboard.press('Enter');
  const search = page.getByRole('searchbox', { name: '站内搜索' });
  await expect(search).toBeVisible();
  await expect(search).toBeFocused();
});

test('source block copies text and links to an immutable official source range', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/site/');

  const source = page.locator('.source-link');
  await expect(source).toHaveAttribute(
    'href',
    `https://github.com/QwenLM/Qwen3-TTS/blob/${SOURCE_COMMIT}/qwen_tts/inference/qwen3_tts_model.py#L83-L87`,
  );
  await page.locator('.copy-source').click();
  await expect(page.locator('.copy-status')).toHaveText('已复制');
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(
    '    def from_pretrained(\n' +
      '        cls,\n' +
      '        pretrained_model_name_or_path: str,\n' +
      '        **kwargs,\n' +
      '    ) -> "Qwen3TTSModel":',
  );

  await expect(page.getByRole('navigation', { name: '相邻章节' })).toBeVisible();
  await expect(page.getByRole('contentinfo')).toContainText('源码引用固定版本');
  const next = page.getByRole('navigation', { name: '相邻章节' }).getByRole('link');
  await expect(next).toHaveAttribute('href', 'guide/migration-boundary.html');
});

test('copy failure leaves a clear manual-copy fallback', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', { value: { writeText: async () => { throw new Error('denied'); } } });
    Document.prototype.execCommand = () => false;
  });
  await page.goto('/site/');
  await page.locator('.copy-source').click();
  await expect(page.locator('.copy-status')).toHaveText('请手动复制');
  await expect(page.locator('pre')).toBeVisible();
});

test('chapter tree exposes the complete ordered path and current page', async ({ page }) => {
  await page.goto('/site/');
  const links = page.locator('#chapter-tree a[data-page-link]');
  await expect(page.locator('.chapter-group-label')).toHaveText([
    '入门教程', '源码深读', '实施路线',
  ]);
  await expect(links).toHaveCount(33);
  await expect(links.first()).toHaveAttribute('aria-current', 'page');
  await expect(links.first()).toContainText('Qwen3-TTS');
  await expect(links.last()).toContainText('实施路线总览');
});

test('without JavaScript the full flow and fallbacks remain readable while enhancements disappear', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1024, height: 768 } });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4173/site/');

  await expect(page.locator('.sidebar-toggle')).toHaveCount(2);
  await expect(page.locator('.sidebar-toggle').first()).toBeHidden();
  await expect(page.locator('.copy-source')).toBeHidden();
  await expect(page.locator('.search-enhancement')).toBeHidden();
  await expect(page.getByRole('searchbox', { name: '站内搜索' })).toBeVisible();
  await expect(page.getByRole('link', { name: '无脚本模式：浏览章节索引' })).toHaveAttribute('href', '#chapter-tree');
  await expect(page.locator('#chapter-tree a[data-page-link]')).toHaveCount(33);
  await expect(page.getByRole('navigation', { name: '章节导航' })).toBeVisible();
  await expect(page.getByRole('main')).toBeVisible();
  await expect(page.getByRole('complementary', { name: '证据与页内目录' })).toBeVisible();
  await page.getByRole('searchbox', { name: '站内搜索' }).fill('RMSNorm');
  await page.getByRole('searchbox', { name: '站内搜索' }).press('Enter');
  await expect(page).toHaveURL(/\/site\/search\.html\?q=RMSNorm$/);
  await context.close();
});

for (const [name, viewport, openDrawer] of [
  ['desktop', { width: 1440, height: 900 }, null],
  ['laptop', { width: 1024, height: 768 }, null],
  ['mobile closed', { width: 390, height: 844 }, null],
  ['mobile chapter drawer', { width: 390, height: 844 }, 'left'],
  ['mobile evidence drawer', { width: 390, height: 844 }, 'right'],
]) {
  test(`${name} has no WCAG A or AA axe violations`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto('/site/');
    if (openDrawer) await page.locator(`#toggle-${openDrawer}`).click();
    await expectWcagAA(page);
  });
}

test('long content, deeper chapter tree, empty evidence, and absent TOC form an axe-clean desktop fixture', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.evaluate(() => {
    document.querySelector('.breadcrumb').textContent = Array(8).fill('超长目录名').join(' / ');
    document.querySelector('h1').textContent = '多机多卡深层目录与极长章节标题'.repeat(4);
    const tree = document.querySelector('#chapter-tree');
    tree.insertAdjacentHTML('beforeend', '<li><ul class="tree-branch"><li><ul class="tree-branch"><li><a href="#source">第六层源码定位路径</a></li></ul></li></ul></li>');
    document.querySelectorAll('#page-toc a').forEach((link) => link.remove());
  });
  await expect(page.getByRole('link', { name: '第六层源码定位路径' })).toBeVisible();
  await expect(page.locator('#page-toc')).toBeHidden();
  await expect(page.getByRole('link', { name: '目录', exact: true })).toBeHidden();
  await expect(page.locator('.evidence-card').first()).toBeVisible();
  await expect(page.locator('.citation-link[data-fixed-source-link]').first()).toBeVisible();
  await expect(page.locator('#toggle-right')).toBeVisible();
  await page.locator('#toggle-right').click();
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'collapsed');
  await expect(page.locator('#article-content')).toBeVisible();
  await expect(page.locator('#evidence-rail')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  await expectWcagAA(page);
});

test('all-empty evidence content removes its rail and toggle and expands the article column', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  const before = await page.locator('#article-content').boundingBox();
  await page.evaluate(() => {
    document.querySelectorAll('[data-rail-content]').forEach((node) => {
      if (node.matches('a')) node.remove();
      else node.textContent = '';
    });
  });
  await expect(page.locator('html')).toHaveAttribute('data-right-content', 'empty');
  await expect(page.locator('#evidence-rail')).toBeHidden();
  await expect(page.locator('#toggle-right')).toBeHidden();
  const after = await page.locator('#article-content').boundingBox();
  expect(after.width).toBeGreaterThan(before.width);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  await expectWcagAA(page);
});

test('200% reflow fixture paints a deep drawer tree without document overflow or axe violations', async ({ page }) => {
  // 1440 CSS pixels at 200% browser zoom yields a 720-pixel layout viewport.
  await page.setViewportSize({ width: 720, height: 900 });
  await page.goto('/site/');
  await page.locator('#toggle-left').click();
  await page.evaluate(() => {
    document.querySelector('.breadcrumb').textContent = Array(8).fill('超长目录名').join(' / ');
    document.querySelector('h1').textContent = '多机多卡深层目录与极长章节标题'.repeat(4);
    const tree = document.querySelector('#chapter-tree');
    tree.insertAdjacentHTML('beforeend', '<li><ul class="tree-branch"><li><ul class="tree-branch"><li><a href="#source">200% 下的第六层路径</a></li></ul></li></ul></li>');
  });
  const deepLink = page.getByRole('link', { name: '200% 下的第六层路径' });
  await expect(deepLink).toBeVisible();
  await deepLink.scrollIntoViewIfNeeded();
  expect(await paintedArea(deepLink)).toBeGreaterThan(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  await expectWcagAA(page);
});

test('print keeps citation URLs and immutable source URLs visible without a page TOC', async ({ page }) => {
  await page.goto('/site/');
  await page.locator('.toc-card').evaluate((node) => node.remove());
  await page.emulateMedia({ media: 'print' });

  const source = page.locator('.source-link');
  await expect(source).toBeVisible();
  await expect.poll(() => source.evaluate((node) => getComputedStyle(node, '::after').content))
    .toContain('github.com/QwenLM/Qwen3-TTS');
  const citation = page.locator('.citation-link[data-fixed-source-link]').first();
  await expect(citation).toBeVisible();
  await expect.poll(() => citation.evaluate((node) => getComputedStyle(node, '::after').content))
    .toContain('github.com/QwenLM/Qwen3-TTS');
  await expect(page.locator('#evidence-rail')).toBeVisible();
});
