import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.getByText('Livraison rapide').click();
  await page.getByRole('button', { name: 'Quels vêtements vendez-vous ?' }).click();
  await page.getByRole('button').filter({ hasText: /^$/ }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).fill('9adeh soum serwel noir');
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).press('Enter');
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).fill('win mawjoudin');
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).press('Enter');
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).click();
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).fill('sel3a mte3kom men touns wal torkiya');
  await page.getByRole('textbox', { name: 'Écrivez votre message...' }).press('Enter');
});