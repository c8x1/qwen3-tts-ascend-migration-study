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
