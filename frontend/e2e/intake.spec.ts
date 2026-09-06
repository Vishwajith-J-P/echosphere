import { expect, test } from '@playwright/test';

test('caller exposes voice-only intake and no text controls', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await page.getByText('தமிழ்', { exact: true }).click();
  await expect(page.getByRole('button', { name: 'Start voice assistance' })).toBeVisible();
  await expect(page.getByText('Voice setup is incomplete.', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: /text demonstration/i })).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Your message' })).toHaveCount(0);
  await expect(page.getByText('Audio only', { exact: true })).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('small screen remains readable and operator route requires login', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 760 });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/caller-mobile.png', fullPage: true });
  await page.goto('/console');
  await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
