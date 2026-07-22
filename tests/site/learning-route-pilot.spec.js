import { expect, test } from '@playwright/test';

test('three pilot surfaces are visible and guides are searchable offline', async ({ page, context }) => {
  await page.goto('/site/index.html');
  await expect(page.getByRole('heading', { name: /三层学习路线图/ })).toBeVisible();

  await page.goto('/site/guide/migration-boundary.html');
  await expect(page.getByRole('heading', { name: '读完能判断什么' })).toBeVisible();
  await expect(page.getByRole('link', { name: /下一页：包结构与推理 API/ })).toBeVisible();

  await page.goto('/site/guide/implementation-route.html');
  await expect(page.getByRole('heading', { name: '六阶段实施路线' })).toBeVisible();
  await expect(page.locator('.evidence-state[data-state="pending_hardware"]').first()).toBeVisible();

  await page.goto('/site/search.html');
  await context.setOffline(true);
  await page.locator('#site-search input[name=q]').fill('迁移边界');
  await page.locator('#site-search').press('Enter');
  await expect(page.locator('#search-results .search-results').getByRole('link', { name: '迁移边界课 · page' })).toBeVisible();
  await page.locator('#site-search input[name=q]').fill('实施路线');
  await page.locator('#site-search').press('Enter');
  await expect(page.locator('#search-results .search-results').getByRole('link', { name: '实施路线总览 · page' })).toBeVisible();
});

test('guide content remains readable without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4173/site/guide/implementation-route.html');
  await expect(page.locator('main article')).toContainText('六阶段实施路线');
  await expect(page.locator('main article')).toContainText('读完能判断什么');
  await context.close();
});
