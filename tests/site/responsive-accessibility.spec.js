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
  await expect(page.locator('#chapter-nav .sidebar-content a').first()).toBeFocused();
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

test('template has no WCAG A or AA accessibility violations', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(results.violations).toEqual([]);
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
