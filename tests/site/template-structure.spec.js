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

  const currentChapter = page.locator('.chapter-nav a.active');
  await expect(currentChapter).toHaveAttribute('aria-current', 'page');
  const markerWidth = await currentChapter.evaluate((node) =>
    Number.parseFloat(getComputedStyle(node).borderInlineStartWidth)
  );
  expect(markerWidth).toBeGreaterThan(0);
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
  const origin = new URL(page.url()).origin;
  expect(resources.every((url) => new URL(url).origin === origin)).toBe(true);
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

test.describe('without JavaScript at tablet width', () => {
  test.use({ javaScriptEnabled: false, viewport: { width: 900, height: 800 } });

  test('evidence region remains readable', async ({ page }) => {
    const evidence = page.getByRole('complementary', { name: '证据与页内目录' });
    await expect(evidence).toBeVisible();

    const box = await evidence.boundingBox();
    expect(box?.width).toBeGreaterThanOrEqual(220);
  });
});
