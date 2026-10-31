import { test, expect } from '@playwright/test';

test('la page se charge', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/.+/);
});

test('envoyer un message au chatbot', async ({ page }) => {
  await page.goto('/');
  const input = page.getByRole('textbox');
  await input.fill('Bonjour');
  await input.press('Enter');
  await expect(page.getByText('Bonjour').first()).toBeVisible();
});