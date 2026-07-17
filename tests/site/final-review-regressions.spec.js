import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const SOURCE_COMMIT = 'b8d8b936f9793aa211baf88b6f501ccbc4aed02b';

async function expectWcagAA(page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
}

test('collapsed rails keep named keyboard-operable destinations with visible tooltips', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.locator('#toggle-left').click();
  await page.locator('#toggle-right').click();

  for (const name of ['首页', '章节', '源码索引', '目录', '证据', '引用']) {
    const link = page.getByRole('link', { name, exact: true });
    await expect(link).toBeVisible();
    await link.focus();
    await expect(link).toBeFocused();
    await expect(link.locator('.rail-tooltip')).toBeVisible();
  }
});

test('mobile header preserves the chapter title and opens a real search input', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/');

  await expect(page.locator('.mobile-chapter-title')).toContainText('HCCL 并行初始化');
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
    `https://github.com/Ascend/MindSpeed/blob/${SOURCE_COMMIT}/mindspeed/core/parallel_state.py#L424-L445`,
  );
  await page.locator('.copy-source').click();
  await expect(page.locator('.copy-status')).toHaveText('已复制');
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toContain('initialize_ndmm_parallel_group');

  await expect(page.getByRole('navigation', { name: '相邻章节' })).toBeVisible();
  await expect(page.getByRole('contentinfo')).toContainText('固定 commit');
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

test('deep chapter tree exposes reusable disclosure state and current path', async ({ page }) => {
  await page.goto('/site/');
  const currentBranch = page.getByRole('button', { name: '分布式初始化' });
  const otherBranch = page.getByRole('button', { name: '训练工程' });
  await expect(currentBranch).toHaveAttribute('aria-expanded', 'true');
  await expect(currentBranch).toHaveAttribute('aria-controls', 'tree-distributed');
  await expect(page.locator('#tree-distributed')).toBeVisible();
  await expect(page.locator('[aria-current="page"]')).toContainText('HCCL');

  await expect(otherBranch).toHaveAttribute('aria-expanded', 'false');
  await otherBranch.focus();
  await page.keyboard.press('Enter');
  await expect(otherBranch).toHaveAttribute('aria-expanded', 'true');
  await expect(page.locator('#tree-training')).toBeVisible();
  await currentBranch.click();
  await expect(page.locator('#tree-distributed')).toBeHidden();
});

test('without JavaScript the full flow and fallbacks remain readable while enhancements disappear', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1024, height: 768 } });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4173/site/');

  await expect(page.locator('.sidebar-toggle')).toHaveCount(2);
  await expect(page.locator('.sidebar-toggle').first()).toBeHidden();
  await expect(page.locator('.tree-toggle').first()).toBeHidden();
  await expect(page.locator('.copy-source')).toBeHidden();
  await expect(page.locator('.search-enhancement')).toBeHidden();
  await expect(page.getByRole('searchbox', { name: '站内搜索' })).toBeVisible();
  await expect(page.getByRole('link', { name: '无脚本模式：浏览章节索引' })).toHaveAttribute('href', '#chapter-tree');
  await expect(page.locator('#tree-distributed')).toBeVisible();
  await expect(page.getByRole('navigation', { name: '章节导航' })).toBeVisible();
  await expect(page.getByRole('main')).toBeVisible();
  await expect(page.getByRole('complementary', { name: '证据与页内目录' })).toBeVisible();
  await page.getByRole('searchbox', { name: '站内搜索' }).fill('HCCL');
  await page.getByRole('searchbox', { name: '站内搜索' }).press('Enter');
  await expect(page).toHaveURL(/\/site\/\?q=HCCL$/);
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

test('long paths, deep headings, empty evidence, and absent page TOC remain usable at 200% zoom', async ({ page }) => {
  // 1024 CSS pixels at 200% browser zoom yields a 512-pixel layout viewport.
  await page.setViewportSize({ width: 512, height: 768 });
  await page.goto('/site/');
  await page.evaluate(() => {
    document.querySelector('.breadcrumb').textContent = Array(8).fill('超长目录名').join(' / ');
    document.querySelector('h1').textContent = '多机多卡深层目录与极长章节标题'.repeat(4);
    document.querySelector('#evidence-rail .sidebar-content').replaceChildren();
  });
  await expect(page.locator('#article-content')).toBeVisible();
  await expect(page.locator('#evidence-rail')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
});

test('print keeps citation URLs and immutable source URLs visible without a page TOC', async ({ page }) => {
  await page.goto('/site/');
  await page.locator('.toc-card').evaluate((node) => node.remove());
  await page.emulateMedia({ media: 'print' });

  await expect(page.locator('.source-link')).toBeVisible();
  await expect(page.locator('.source-link')).toHaveCSS('--print-url', /github\.com\/Ascend\/MindSpeed/);
  await expect(page.locator('.citation-link')).toBeVisible();
  await expect(page.locator('.citation-link')).toHaveCSS('--print-url', /github\.com\/Ascend\/MindSpeed/);
  await expect(page.locator('#evidence-rail')).toBeVisible();
});
