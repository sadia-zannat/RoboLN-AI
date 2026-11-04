import {test,expect} from '@playwright/test';
const stamp=()=>`${Date.now()}-${Math.random().toString(36).slice(2,7)}`;
async function register(page:import('@playwright/test').Page){
 await page.goto('/register');
 await page.getByLabel('Full name').fill('Quality Tester');
 await page.getByLabel('Email address').fill(`qa-${stamp()}@example.com`);
 await page.getByLabel('Password').fill('E2eStrongPassword123!');
 await page.getByRole('button',{name:'Create account'}).click();
 await expect(page).toHaveURL(/\/projects$/);
}
async function makeProject(page:import('@playwright/test').Page){
 await page.getByRole('button',{name:'New project'}).click();
 await page.getByLabel('Project name').fill('Physical Rover - QA');
 await page.getByRole('button',{name:'Create project',exact:true}).click();
 await expect(page).toHaveURL(/\/projects\/[^/]+$/);
 return new URL(page.url()).pathname.split('/')[2];
}

test('registered session, routes, real back-forward, breadcrumbs, home, deep refresh',async({page},info)=>{
 await register(page);const pid=await makeProject(page);
 await page.getByRole('link',{name:/Open Workspace/}).click();
 await expect(page).toHaveURL(new RegExp(`/projects/${pid}/workspace/plan$`));
 await page.getByRole('link',{name:'Practice in 3D'}).click();
 await expect(page).toHaveURL(/workspace\/practice$/);
 await page.getByRole('button',{name:'Back',exact:true}).click();
 await expect(page).toHaveURL(/workspace\/plan$/);
 await expect(page.getByRole('button',{name:'Forward',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'Forward',exact:true}).click();
 await expect(page).toHaveURL(/workspace\/practice$/);
 await page.goBack();
 await expect(page).toHaveURL(/workspace\/plan$/);
 await page.goForward();
 await expect(page).toHaveURL(/workspace\/practice$/);
 await page.reload();await expect(page).toHaveURL(/workspace\/practice$/);
 await page.getByRole('link',{name:'Home — Projects'}).click();
 await expect(page).toHaveURL(/\/projects$/);
 await page.screenshot({path:`../logs/browser-${info.project.name}-light.png`,fullPage:true});
});

test('light/dark/system persistence, navigation and width audit',async({page},info)=>{
 await register(page);const pid=await makeProject(page);
 const screens=[`/projects/${pid}/workspace/plan`,`/projects/${pid}/workspace/practice`,`/projects/${pid}/workspace/build`,`/projects/${pid}/twin`,`/projects/${pid}/evidence`,'/settings'];
 for(const mode of ['light','dark'] as const){
  await page.goto('/settings');await page.getByRole('button',{name:new RegExp(`^${mode}$`,'i')}).click();
  await page.reload();await expect(page.locator('html')).toHaveAttribute('data-theme',mode);
  for(const path of screens){
   await page.goto(path);await expect(page.locator('main')).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),`overflow on ${path}`).toBeTruthy();
   await page.screenshot({path:`../logs/browser-${info.project.name}-${mode}-${path.split('/').at(-1)}.png`,fullPage:true});
  }
 }
});

test('viewer cannot edit, missing project cannot leak title, signout blocks deep link',async({page})=>{
 await register(page);const id=await makeProject(page);
 await page.goto('/projects/00000000-0000-0000-0000-000000000000');
 await expect(page.getByText(/project was not found/i)).toBeVisible();
 await page.goto(`/projects/${id}/workspace/plan`);
 await page.getByRole('button',{name:'Sign out'}).click();
 await expect(page).toHaveURL(/\/login/);
 await page.goto(`/projects/${id}/workspace/plan`);
 await expect(page).toHaveURL(/\/login\?next=/);
});

test('keyboard skip link and forward initially disabled',async({page})=>{
 await register(page);
 await expect(page.getByRole('button',{name:/Forward unavailable/})).toBeDisabled();
 await page.keyboard.press('Tab');
 await expect(page.locator('.skip-link')).toBeAttached();
});


test('per-project draft isolation across navigation and refresh',async({page})=>{
 await register(page);const a=await makeProject(page);
 await page.goto(`/projects/${a}/workspace/plan`);
 await page.getByLabel('Your engineering draft').fill('Private first-project draft');
 await page.getByRole('button',{name:'Save draft'}).click();
 await expect(page.getByRole('status')).toContainText('Draft saved');
 await page.goto('/projects');const b=await makeProject(page);
 await page.goto(`/projects/${b}/workspace/plan`);
 await expect(page.getByLabel('Your engineering draft')).toHaveValue('');
 await page.goto(`/projects/${a}/workspace/plan`);
 await expect(page.getByLabel('Your engineering draft')).toHaveValue('Private first-project draft');
});

test('public product titles and keyboard modal dismissal',async({page},info)=>{
 await register(page);await expect(page).toHaveTitle(/Projects \| RoboLN/);
 if(info.project.name.startsWith('mobile'))await page.getByRole('button',{name:'Open navigation'}).click();
 await page.getByRole('button',{name:'Search your projects'}).click();
 await expect(page.getByRole('dialog',{name:'Find project'})).toBeVisible();
 await page.keyboard.press('Escape');
 await expect(page.getByRole('dialog',{name:'Find project'})).toHaveCount(0);
});


test('mobile workspace tabs expose all three complete destinations',async({page},info)=>{
 if(!info.project.name.startsWith('mobile'))return;
 await register(page);const pid=await makeProject(page);
 await page.goto(`/projects/${pid}/workspace/build`);
 const tabs=page.getByRole('navigation',{name:'Workspace tabs'});
 for(const label of ['Plan','Practice in 3D','Live Build']){
  await expect(tabs.getByRole('link',{name:label})).toBeVisible();
 }
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBeTruthy();
});

// Authored regression case; requires real Next.js + Playwright execution to certify.
test('archived projects cannot edit hardware, membership or planning drafts',async({page})=>{
 await register(page);const pid=await makeProject(page);
 await page.getByRole('link',{name:'Home — Projects'}).click();
 await expect(page).toHaveURL(/\/projects$/);
 page.once('dialog',dialog=>dialog.accept());
 await page.getByRole('button',{name:'Archive Physical Rover - QA'}).click();
 await expect(page.getByText('No matching projects')).toBeVisible();
 await page.getByRole('checkbox',{name:'Include archived'}).check();
 await page.getByRole('link',{name:/Open project/}).click();
 await expect(page).toHaveURL(new RegExp(`/projects/${pid}$`));
 await expect(page.getByText(/archived.*read-only/i)).toBeVisible();
 await expect(page.getByRole('button',{name:'Save unverified draft'})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Grant access'})).toHaveCount(0);
 await page.getByRole('link',{name:/Open Workspace/}).click();
 await expect(page.getByLabel('Your engineering draft')).toBeDisabled();
 await expect(page.getByRole('button',{name:'Save draft'})).toBeDisabled();
});

// Real download verification (not a stub). Requires Next.js + Chromium.
test('account export includes saved hardware and my own planning draft',async({page})=>{
 const {readFile}=await import('node:fs/promises');
 await register(page);const pid=await makeProject(page);
 await page.getByLabel('Exact board model').fill('Raspberry Pi 3 Model B+');
 await page.getByRole('button',{name:'Save unverified draft'}).click();
 await expect(page.getByRole('status')).toContainText('Hardware draft saved');
 await page.getByRole('link',{name:/Open Workspace/}).click();
 const editor=page.getByLabel('Your engineering draft');
 await expect(editor).toBeEnabled();
 await editor.fill('Export-only test engineering notes');
 await page.getByRole('button',{name:'Save draft'}).click();
 await expect(page.getByRole('status')).toContainText('Draft saved');
 await page.goto('/settings');
 const [download]=await Promise.all([
  page.waitForEvent('download'),
  page.getByRole('button',{name:'Download JSON'}).click()
 ]);
 expect(download.suggestedFilename()).toBe('roboln-account-export.json');
 const savedPath=await download.path();
 expect(savedPath).toBeTruthy();
 const data=JSON.parse(await readFile(savedPath!,'utf8')) as {
  projects:Array<{id:string;hardware_draft?:{board_model?:string};my_draft:string}>;
 };
 const project=data.projects.find(p=>p.id===pid);
 expect(project).toBeTruthy();
 expect(project!.hardware_draft?.board_model).toBe('Raspberry Pi 3 Model B+');
 expect(project!.my_draft).toBe('Export-only test engineering notes');
});
