import { test, expect } from '@playwright/test';
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  sleep(2000);
  await expect(page.getByText('IA Active')).toBeVisible()
  await page.getByRole('button', { name: 'Quels vêtements vendez-vous ?' }).click();
  await page.getByRole('button', { name: 'Quels vêtements vendez-vous ?' }).press('ArrowDown');
  await page.getByRole('button').filter({ hasText: /^$/ }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).fill('9adeh soum chemise');
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).press('Enter');
  await page.getByText('Paiement sécurisé').click();
  await page.getByRole('link', { name: 'Administration' }).click();
  await page.locator('body').press('ArrowDown');
  await page.locator('body').press('ArrowDown');
  await page.locator('body').press('ArrowDown');
  await page.locator('body').press('ArrowDown');
  await page.locator('body').press('ArrowDown');
  await page.locator('body').press('ArrowDown');
  await page.locator('body').press('ArrowDown');
  await page.locator('body').press('ArrowUp');
  await page.locator('body').press('ArrowUp');
  await page.locator('body').press('ArrowUp');
  await page.locator('body').press('ArrowUp');
  await page.locator('body').press('ArrowUp');
  await page.getByRole('link', { name: 'Retour à la boutique' }).click();
  await page.locator('body').press('ArrowDown');
});