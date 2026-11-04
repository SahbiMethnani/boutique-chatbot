import { test, expect } from '@playwright/test';
import { Buffer } from 'node:buffer';

test('importer un fichier CSV depuis la page admin', async ({ page }) => {
  await page.route('http://localhost:8000/admin/import-products-csv', async (route) => {
    expect(route.request().headers()['x-admin-key']).toBe('cle-admin-test');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: '2 produits importés avec succès.',
        imported: 2,
      }),
    });
  });

  await page.goto('/admin');
  await expect(page.getByRole('heading', { name: 'Importer le catalogue' })).toBeVisible();
  await page.getByLabel('Clé d’administration').fill('cle-admin-test');
  await page.getByLabel('Fichier de produits').setInputFiles({
    name: 'produits.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from(
      'nom,description,prix,categorie,tailles,couleurs,stock\nRobe,Legere,89.9,Robes,S|M,Blanc,4',
    ),
  });
  await page.getByRole('button', { name: 'Importer les produits' }).click();

  await expect(page.getByRole('status')).toContainText('2 produits importés avec succès.');
});
