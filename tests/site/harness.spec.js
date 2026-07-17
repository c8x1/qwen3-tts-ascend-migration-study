import { expect, test } from '@playwright/test';

test('browser harness runs JavaScript', async ({ page }) => {
  await page.setContent('<main><h1>Harness</h1></main>');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Harness');
});
