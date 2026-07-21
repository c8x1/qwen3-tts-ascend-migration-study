import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

async function expectNoAxeViolations(page) {
  const result = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(result.violations, JSON.stringify(result.violations, null, 2)).toEqual([]);
}

test('desktop architecture page is WCAG A/AA clean', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/target/model-architecture.html');
  await expectNoAxeViolations(page);
});

test('laptop data page is WCAG A/AA clean', async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto('/site/target/sft-data-collate.html');
  await expectNoAxeViolations(page);
});

test('mobile coverage drawers remain accessible', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/target/coverage-gaps.html');
  await page.locator('#toggle-left').click();
  await expect(page.locator('#chapter-nav')).toBeVisible();
  await expectNoAxeViolations(page);
  await page.locator('#toggle-left').click();
  await page.locator('#toggle-right').click();
  await expect(page.locator('#evidence-rail')).toBeVisible();
  await expectNoAxeViolations(page);
});

test('JavaScript-disabled site retains article evidence and static directory', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('/site/search.html');
  await expect(page.locator('#article-content')).toContainText('全站搜索');
  await expect(page.locator('#no-script-index a')).toHaveCount(31);
  await page.goto('/site/target/model-architecture.html');
  await expect(page.locator('#article-content')).toContainText('模型');
  await expect(page.locator('#evidence-rail a[href^="https://"]')).not.toHaveCount(0);
  await context.close();
});

test('720 CSS pixels at 200 percent has no document overflow', async ({ page }) => {
  await page.setViewportSize({ width: 720, height: 800 });
  await page.goto('/site/target/coverage-gaps.html');
  await expect(page.locator('.table-scroll')).not.toHaveCount(0);
  const metrics = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
    tableScrollable: [...document.querySelectorAll('.table-scroll')]
      .some((node) => node.scrollWidth > node.clientWidth),
  }));
  expect(metrics.scroll).toBeLessThanOrEqual(metrics.client);
  expect(metrics.tableScrollable).toBe(true);
});
