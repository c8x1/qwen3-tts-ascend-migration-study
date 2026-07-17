import { expect, test } from '@playwright/test';

for (const [name, viewport] of Object.entries({
  desktop: { width: 1440, height: 900 },
  laptop: { width: 1024, height: 768 },
  mobile: { width: 390, height: 844 },
})) {
  test(`${name} template matches approved baseline`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto('/site/');
    await expect(page).toHaveScreenshot(`${name}-template.png`, {
      fullPage: true,
      animations: 'disabled',
      maxDiffPixelRatio: 0.01,
    });
  });
}
