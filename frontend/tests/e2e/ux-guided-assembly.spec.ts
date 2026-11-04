import {test,expect,type Page} from '@playwright/test';

async function project(page:Page){
 await page.goto('/register');
 await page.getByLabel('Full name').fill('UX QA Tester');
 await page.getByLabel('Email address').fill(`ux-${Date.now()}-${Math.random().toString(36).slice(2,8)}@example.com`);
 await page.getByLabel('Password').fill('RoboLnTestingPassword123!');
 await page.getByRole('button',{name:'Create account'}).click();
 await page.getByRole('button',{name:'New project'}).click();
 await page.getByLabel('Project name').fill('User friendly assembly QA');
 await page.getByRole('button',{name:'Create project',exact:true}).click();
 await expect(page).toHaveURL(/\/projects\/[^/]+$/);
 return new URL(page.url()).pathname;
}

test('tutorial, drag from component library and revision persistence',async({page})=>{
 const root=await project(page);await page.goto(root+'/workspace/practice');
 await expect(page.getByTestId('robot-scene')).toHaveAttribute('data-ready','true');
 await expect(page.getByText('Build it step by step')).toBeVisible();
 await page.getByLabel('Component library',{exact:true}).selectOption('camera');
 const scene=page.getByTestId('robot-scene');const bounds=await scene.boundingBox();expect(bounds).not.toBeNull();
 await page.locator('.iw-drag-source').dragTo(scene,{targetPosition:{x:bounds!.width*.6,y:bounds!.height*.45}});
 await expect(page.getByRole('heading',{name:'Inspect: Inspection camera'})).toBeVisible();
 await expect(page.getByText('Part placed in the scene. Adjust / attach it, then save the assembly revision.')).toBeVisible();
 await page.getByRole('button',{name:'Save assembly revision',exact:true}).click();
 await expect(page.getByText('Scene changes saved as a user-confirmed engineering revision.')).toBeVisible();
 await page.reload();
 await expect(page.getByRole('button',{name:'Inspection camera · UNKNOWN'})).toBeVisible();
});

test('drag existing part, attach parent, and preserve translated grouping',async({page})=>{
 const root=await project(page);await page.goto(root+'/workspace/plan');
 await page.getByRole('button',{name:'Load provisional rover draft'}).click();
 await page.getByRole('button',{name:'Save engineering workspace',exact:true}).click();
 await expect(page.getByText('Engineering workspace saved · revision 1')).toBeVisible();
 await page.goto(root+'/workspace/practice');
 await page.getByRole('button',{name:'Inspection camera · UNKNOWN'}).click();
 await page.getByLabel('Assembly parent').selectOption('board');
 await page.getByRole('button',{name:'Place above parent'}).click();
 const original=Number(await page.getByLabel('Position x').inputValue());
 const scene=page.getByTestId('robot-scene');await expect(scene).toHaveAttribute('data-ready','true');
 const bounds=await scene.boundingBox();expect(bounds).not.toBeNull();
 await page.getByRole('button',{name:'Inspection camera · UNKNOWN',exact:true}).dragTo(scene,{targetPosition:{x:bounds!.width*.7,y:bounds!.height*.6}});
 await expect(page.getByRole('status')).toContainText('Part repositioned');
 const x=await page.getByLabel('Position x').inputValue();expect(Number(x)).not.toBe(original);
 await page.getByRole('button',{name:'Save assembly revision',exact:true}).click();
 await expect(page.getByText('Scene changes saved as a user-confirmed engineering revision.')).toBeVisible();
 await page.reload();
 await page.getByRole('button',{name:'Inspection camera · UNKNOWN'}).click();
 await expect(page.getByLabel('Position x')).toHaveValue(x);
 const w=await (await page.request.get('/api'+root+'/workbench')).json();
 expect(w.data.parts.find((c:{id:string})=>c.id==='camera').parent_id).toBe('board');
 const before=w.data.parts.find((c:{id:string})=>c.id==='camera');
 const board=w.data.parts.find((c:{id:string})=>c.id==='board');
 await page.getByRole('button',{name:'Controller board · UNKNOWN',exact:true}).click();
 await page.getByLabel('Position x').fill(String(board.x+1));
 await page.getByRole('button',{name:'Save assembly revision',exact:true}).click();
 await expect(page.getByText('Scene changes saved as a user-confirmed engineering revision.')).toBeVisible();
 await page.reload();
 const moved=await (await page.request.get('/api'+root+'/workbench')).json();
 expect(moved.data.parts.find((c:{id:string})=>c.id==='camera').x).toBeCloseTo(before.x+1);
});

test('model message renders headings/lists/code without interpreting HTML',async({page})=>{
 const root=await project(page);
 await page.route('**/ai/messages',async route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{
  id:'test-msg',question:'Show my plan',answer:'### Plan\n\n- **First** check sensor\n- Then test\n\n```text\nSAFE_DEMO_ONLY\n```\n\n<img src=x onerror=alert(1)>',model:'muse-spark-1.3',provider_id:'mock-test-provider',sources:[],created_at:new Date().toISOString(),image_included:false
 }])}));
 await page.goto(root+'/workspace/plan');
 await expect(page.getByRole('heading',{name:'Plan your build',exact:true})).toBeVisible();
 await expect(page.locator('.rich-answer li').first()).toContainText('First check sensor');
 await expect(page.locator('.rich-answer pre')).toContainText('SAFE_DEMO_ONLY');
 await expect(page.locator('.rich-answer img')).toHaveCount(0);
 await expect(page.locator('.rich-answer')).toContainText('<img src=x onerror=alert(1)>');
});
