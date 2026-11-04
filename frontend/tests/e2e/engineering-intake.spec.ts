import {test,expect} from '@playwright/test';
const email=()=>`engineering-${Date.now()}-${Math.random().toString(36).slice(2,8)}@example.com`;
async function onboarding(page:import('@playwright/test').Page){
 await page.goto('/register');
 await page.getByLabel('Full name').fill('Engineering QA');
 await page.getByLabel('Email address').fill(email());
 await page.getByLabel('Password').fill('E2eStrongPassword123!');
 await page.getByRole('button',{name:'Create account'}).click();
 await page.getByRole('button',{name:'New project'}).click();
 await page.getByLabel('Project name').fill('Planning QA rover');
 await page.getByRole('button',{name:'Create project',exact:true}).click();
 await page.getByRole('link',{name:/Open Workspace/}).click();
}
test('engineering intake creates isolated, unverified, versioned draft',async({page})=>{
 await onboarding(page);
 await expect(page.getByRole('region',{name:'Engineering intake and revisioned plans'})).toBeVisible();
 await page.getByLabel('Project family').selectOption('obstacle_alarm');
 await page.getByLabel('Engineering goal').fill('Measure a distance and display an alert on a low-voltage educational device');
 await page.getByRole('button',{name:'Generate reviewable draft'}).click();
 await expect(page.getByText('Saved: revision 1')).toBeVisible();
 await expect(page.getByText('Hardware verification: NOT VERIFIED')).toBeVisible();
 await expect(page.getByText('Exact board model is not identified')).toBeVisible();
 await expect(page.getByText('Physical actuation remains HOLD.',{exact:false})).toBeVisible();
 await page.reload();
 await expect(page.getByText('Saved: revision 1')).toBeVisible();
 // At tablet widths the persistent sidebar is hidden; use the real drawer navigation.
 const width = page.viewportSize()?.width ?? 1440;
 if (width >= 768 && width <= 1023) {
  await page.getByRole('button',{name:'Open navigation'}).click();
  await page.getByRole('dialog',{name:'Navigation'}).getByRole('link',{name:'Evidence',exact:true}).click();
 } else {
  await page.getByRole('link',{name:'Evidence',exact:true}).first().click();
 }
 await expect(page.getByText('Engineering draft revision saved — unverified')).toBeVisible();
});
test('camera starts disabled without permission and offers deliberate control',async({page})=>{
 await onboarding(page);
 await page.getByRole('link',{name:'Live Build'}).first().click();
 await expect(page.getByText('Camera not broadcasting')).toBeVisible();
 await expect(page.getByRole('button',{name:'Enable camera'})).toBeEnabled();
 await expect(page.getByText('No approved assembly step is inferred from camera frames.',{exact:false})).toBeVisible();
});
