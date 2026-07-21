import { expect, test } from '@playwright/test';

test('reference and mapping pages expose textual evidence states', async ({ page }) => {
  await page.goto('/site/reference/mm-config.html');
  await expect(page.locator('.evidence-state').first()).toContainText(/已核验|项目声明|静态推断|待真机验证/);
  await expect(page.locator('[data-fixed-source-link]').first()).toHaveAttribute('href', /0edd553e/);
  await page.goto('/site/mapping/map-hardware.html');
  await expect(page.getByText('通过条件')).toBeVisible();
});

test('local search finds reference and mapping chapters offline', async ({ page, context }) => {
  await page.goto('/site/search.html');
  await context.setOffline(true);
  await page.locator('#site-search input[name=q]').fill('MM 配置');
  await page.locator('#site-search').press('Enter');
  await expect(page.getByRole('status')).toContainText('找到');
  await expect(page.locator('#search-results .search-results').getByRole('link', { name: /MM 配置入口/ })).toBeVisible();
});

test('reference chapter remains readable without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4173/site/reference/moss-training.html');
  await expect(page.locator('main article')).toContainText('训练');
  await context.close();
});
