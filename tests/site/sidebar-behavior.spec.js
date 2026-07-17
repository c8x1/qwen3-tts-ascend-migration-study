import { expect, test } from '@playwright/test';

test('wide desktop toggles each sidebar independently and synchronizes labels', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  const root = page.locator('html');
  const left = page.locator('#toggle-left');
  const right = page.locator('#toggle-right');

  await expect(root).toHaveAttribute('data-left-sidebar', 'expanded');
  await expect(root).toHaveAttribute('data-right-sidebar', 'expanded');
  await expect(left).toHaveAttribute('aria-label', '收起章节导航');
  await expect(right).toHaveAttribute('aria-label', '收起证据栏');

  await left.click();
  await expect(root).toHaveAttribute('data-left-sidebar', 'collapsed');
  await expect(root).toHaveAttribute('data-right-sidebar', 'expanded');
  await expect(left).toHaveAttribute('aria-expanded', 'false');
  await expect(left).toHaveAttribute('aria-label', '展开章节导航');
  await expect(right).toHaveAttribute('aria-expanded', 'true');
  await expect(right).toHaveAttribute('aria-label', '收起证据栏');

  await right.click();
  await expect(root).toHaveAttribute('data-left-sidebar', 'collapsed');
  await expect(root).toHaveAttribute('data-right-sidebar', 'collapsed');
  await expect(right).toHaveAttribute('aria-expanded', 'false');
  await expect(right).toHaveAttribute('aria-label', '展开证据栏');
});

test('laptop defaults right collapsed and persists both preferences independently', async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto('/site/');
  const root = page.locator('html');

  await expect(root).toHaveAttribute('data-left-sidebar', 'expanded');
  await expect(root).toHaveAttribute('data-right-sidebar', 'collapsed');
  await page.locator('#toggle-left').click();
  await page.locator('#toggle-right').click();
  await page.reload();
  await expect(root).toHaveAttribute('data-left-sidebar', 'collapsed');
  await expect(root).toHaveAttribute('data-right-sidebar', 'expanded');

  await page.locator('#toggle-left').click();
  await page.reload();
  await expect(root).toHaveAttribute('data-left-sidebar', 'expanded');
  await expect(root).toHaveAttribute('data-right-sidebar', 'expanded');
});

test('invalid preferences are removed and recover to viewport defaults', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.evaluate(() => {
    localStorage.setItem('q3a.sidebar.left', 'broken');
    localStorage.setItem('q3a.sidebar.right', 'broken');
  });
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'expanded');
  await expect(page.locator('html')).toHaveAttribute('data-right-sidebar', 'expanded');
  expect(await page.evaluate(() => ({
    left: localStorage.getItem('q3a.sidebar.left'),
    right: localStorage.getItem('q3a.sidebar.right'),
  }))).toEqual({ left: null, right: null });
});

test('keyboard shortcuts update root state, labels, and independent sides', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  const root = page.locator('html');
  const left = page.locator('#toggle-left');
  const right = page.locator('#toggle-right');

  await page.keyboard.press('Alt+[');
  await expect(root).toHaveAttribute('data-left-sidebar', 'collapsed');
  await expect(root).toHaveAttribute('data-right-sidebar', 'expanded');
  await expect(left).toHaveAttribute('aria-expanded', 'false');
  await expect(left).toHaveAttribute('aria-label', '展开章节导航');
  await expect(right).toHaveAttribute('aria-expanded', 'true');
  await expect(right).toHaveAttribute('aria-label', '收起证据栏');

  await page.keyboard.press('Alt+]');
  await expect(root).toHaveAttribute('data-left-sidebar', 'collapsed');
  await expect(root).toHaveAttribute('data-right-sidebar', 'collapsed');
  await expect(right).toHaveAttribute('aria-expanded', 'false');
  await expect(right).toHaveAttribute('aria-label', '展开证据栏');
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

test('setItem-only failure keeps memory authoritative across resizes', async ({ page }) => {
  await page.addInitScript(() => {
    Storage.prototype.setItem = () => { throw new Error('storage writes disabled'); };
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.locator('#toggle-left').click();
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'collapsed');

  await page.setViewportSize({ width: 1024, height: 768 });
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'collapsed');
  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'collapsed');
});

test('breakpoint round-trip preserves desktop preference and labels', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/');
  await page.locator('#toggle-left').click();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#toggle-left')).toHaveAttribute('aria-expanded', 'false');
  await expect(page.locator('#toggle-left')).toHaveAttribute('aria-label', '打开章节导航');

  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.locator('html')).toHaveAttribute('data-left-sidebar', 'collapsed');
  await expect(page.locator('#toggle-left')).toHaveAttribute('aria-expanded', 'false');
  await expect(page.locator('#toggle-left')).toHaveAttribute('aria-label', '展开章节导航');
});

test('mobile triggers stay accessible and same-side activation closes the drawer', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/');
  const root = page.locator('html');
  const left = page.locator('#toggle-left');

  await expect(page.locator('#chapter-nav')).toHaveAttribute('inert', '');
  await expect(page.locator('#evidence-rail')).toHaveAttribute('inert', '');
  await expect(left).toBeVisible();
  await left.focus();
  await expect(left).toBeFocused();
  await expect(left).toHaveAttribute('aria-expanded', 'false');
  await expect(left).toHaveAttribute('aria-label', '打开章节导航');

  await left.click();
  await expect(root).toHaveAttribute('data-drawer-open', 'left');
  await expect(left).toHaveAttribute('aria-expanded', 'true');
  await expect(left).toHaveAttribute('aria-label', '关闭章节导航');

  await left.click();
  await expect(root).not.toHaveAttribute('data-drawer-open', /.+/);
  await expect(page.locator('.drawer-backdrop')).toBeHidden();
  await expect(left).toBeFocused();
  await expect(left).toHaveAttribute('aria-expanded', 'false');
  await expect(left).toHaveAttribute('aria-label', '打开章节导航');

  await page.keyboard.press('Alt+[');
  await expect(root).toHaveAttribute('data-drawer-open', 'left');
  await expect(left).toHaveAttribute('aria-label', '关闭章节导航');
  await page.keyboard.press('Alt+[');
  await expect(root).not.toHaveAttribute('data-drawer-open', /.+/);
  await expect(left).toBeFocused();
  await expect(left).toHaveAttribute('aria-label', '打开章节导航');
});

test('mobile switching sides closes the old drawer and synchronizes both triggers', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/');
  const root = page.locator('html');
  const left = page.locator('#toggle-left');
  const right = page.locator('#toggle-right');

  await left.click();
  await expect(root).toHaveAttribute('data-drawer-open', 'left');
  await expect(page.locator('#chapter-nav')).not.toHaveAttribute('inert', '');
  await expect(page.locator('#evidence-rail')).toHaveAttribute('inert', '');

  await right.click();
  await expect(root).toHaveAttribute('data-drawer-open', 'right');
  await expect(page.locator('#chapter-nav')).toHaveAttribute('inert', '');
  await expect(page.locator('#evidence-rail')).not.toHaveAttribute('inert', '');
  await expect(left).toHaveAttribute('aria-expanded', 'false');
  await expect(left).toHaveAttribute('aria-label', '打开章节导航');
  await expect(right).toHaveAttribute('aria-expanded', 'true');
  await expect(right).toHaveAttribute('aria-label', '关闭证据栏');
});
