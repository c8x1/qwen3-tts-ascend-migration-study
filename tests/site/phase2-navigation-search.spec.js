import { expect, test } from '@playwright/test';

test('all Phase 3 pages are reachable through chapter navigation', async ({ page }) => {
  await page.goto('/site/');
  await expect(page.locator('#chapter-tree a[data-page-link]')).toHaveCount(31);
});

test('previous and next links form a non-cyclic ordered path', async ({ page }) => {
  await page.goto('/site/target/model-architecture.html');
  const adjacent = page.getByRole('navigation', { name: '相邻章节' }).getByRole('link');
  await expect(adjacent.first()).toHaveAttribute('href', 'package-inference-api.html');
  await expect(adjacent.last()).toHaveAttribute('href', 'tokenizer-12hz.html');
});

test('loaded site keeps inline search working after browser goes offline', async ({ page, context }) => {
  const requests = [];
  page.on('request', (request) => requests.push(request.url()));
  await page.goto('/site/search.html');
  await context.setOffline(true);
  await page.locator('#site-search input[name=q]').fill('forward_sub_talker_finetune');
  await page.locator('#site-search').press('Enter');
  await expect(page.getByRole('status')).toContainText('找到');
  await expect(page.getByRole('link', { name: /forward_sub_talker_finetune/ }).first()).toBeVisible();
  expect(requests.every((url) => new URL(url).origin === new URL(page.url()).origin)).toBe(true);
});

test('nested target search form resolves to root search results', async ({ page }) => {
  await page.goto('/site/target/model-architecture.html');
  await page.locator('#site-search input[name=q]').fill('RMSNorm');
  await Promise.all([
    page.waitForURL(/\/site\/search\.html\?q=RMSNorm$/),
    page.locator('#site-search').press('Enter'),
  ]);
  await expect(page.getByRole('status')).toContainText('找到');
});

test('file and config indexes expose all snapshots without source bodies', async ({ page }) => {
  await page.goto('/site/indexes/source-files.html');
  const snapshots = await page.locator('[data-fixed-source-link]')
    .evaluateAll((links) => [...new Set(links.map((link) => link.dataset.snapshotId))].sort());
  expect(snapshots).toHaveLength(4);
  await page.goto('/site/indexes/symbols-configs.html');
  const targetClass = page.locator(
    'a[data-snapshot-id="qwen3-tts-022e286b"]' +
    '[data-source-path="qwen_tts/core/models/modeling_qwen3_tts.py"]' +
    '[data-start-line="1813"][data-end-line="2292"]',
  ).locator('xpath=ancestor::tr');
  await expect(targetClass).toContainText('Qwen3TTSForConditionalGeneration');
  await expect(page.locator('[data-source-body]')).toHaveCount(0);
});

test('coverage page exposes all target dispositions and future interfaces', async ({ page }) => {
  await page.goto('/site/target/coverage-gaps.html');
  await expect(page.locator('[data-coverage-path]')).toHaveCount(35);
  await expect(page.getByText('MindSpeed-MM 完整走读')).toBeVisible();
  await expect(page.locator('#environment-lanes p').first()).toContainText('CANN 8.5.2 兼容性：unknown');
});
