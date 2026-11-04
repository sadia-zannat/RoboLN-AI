import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
async function setup(page:Page){
 await page.goto('/register');await page.getByLabel('Full name').fill('Final QA User');await page.getByLabel('Email address').fill(`final-${Date.now()}-${Math.random().toString(36).slice(2,8)}@example.com`);await page.getByLabel('Password').fill('FinalQaPassword123!');await page.getByRole('button',{name:'Create account'}).click();await expect(page).toHaveURL(/\/projects$/);
 await page.getByRole('button',{name:'New project'}).click();await page.getByLabel('Project name').fill('Complete QA rover');await page.getByRole('button',{name:'Create project',exact:true}).click();await expect(page).toHaveURL(/\/projects\/[^/]+$/);return new URL(page.url()).pathname;
}
async function saveRover(page:Page,root:string){await page.goto(root+'/workspace/plan');await page.getByRole('button',{name:'Load provisional rover draft'}).click();await page.getByRole('button',{name:'Save engineering workspace',exact:true}).click();await expect(page.getByText('Engineering workspace saved · revision 1')).toBeVisible();}

test('source ingestion retrieval and honest AI not-configured error',async({page})=>{
 const root=await setup(page);await page.goto(root+'/workspace/plan');
 await page.getByLabel('Technical source file').setInputFiles({name:'review-reference.txt',mimeType:'text/plain',buffer:Buffer.from('Calibration reference. Soil moisture readings require dry and wet physical samples. Signal label SIG must be reviewed.')});
 await page.getByRole('button',{name:'Upload source',exact:true}).click();await expect(page.getByRole('button',{name:'review-reference.txt · v1'})).toBeVisible();
 await page.getByLabel('Search source text').fill('calibration');await page.getByRole('button',{name:'Retrieve excerpts'}).click();await expect(page.getByText('Calibration reference. Soil moisture readings require dry and wet physical samples. Signal label SIG must be reviewed.',{exact:true}).first()).toBeVisible();
 await page.getByLabel('New component',{exact:true}).fill('Referenced sensor');await page.getByRole('button',{name:'Add component',exact:true}).click();await expect(page.getByLabel('Reference source')).toContainText('review-reference.txt v1');await page.getByLabel('Reference source').selectOption({label:'review-reference.txt v1'});await page.getByRole('button',{name:'review-reference.txt · v1'}).click();await expect(page.getByText(/SHA-256:/)).toBeVisible();
 await expect(page.getByText('NOT_CONFIGURED',{exact:true})).toBeVisible();await page.getByLabel('Allow my project context and question to be sent to Meta Model API').check();await page.getByLabel('Ask a project question').fill('Which calibration evidence is missing?');await page.getByRole('button',{name:'Ask Meta AI',exact:true}).click();await expect(page.getByRole('alert').filter({hasText:'NOT_CONFIGURED'})).toContainText('NOT_CONFIGURED');await expect(page.getByLabel('AI conversation')).toContainText('No provider responses yet');
});

test('engineering revision interactive WebGL selection and manual scene correspondence',async({page})=>{
 const root=await setup(page);await saveRover(page,root);await page.goto(root+'/workspace/practice');
 await expect(page.getByTestId('robot-scene')).toHaveAttribute('data-ready','true');await expect(page.locator('canvas')).toBeVisible();
 const canvas=page.locator('canvas');const before=await canvas.screenshot();const bounds=await canvas.boundingBox();expect(bounds).not.toBeNull();await page.mouse.move(bounds!.x+bounds!.width*0.7,bounds!.y+bounds!.height*0.5);await page.mouse.down();await page.mouse.move(bounds!.x+bounds!.width*0.35,bounds!.y+bounds!.height*0.65,{steps:12});await page.mouse.up();await page.mouse.wheel(0,120);await expect.poll(async()=>Buffer.compare(before,await canvas.screenshot())).not.toBe(0);
 await page.getByRole('button',{name:'Controller board · UNKNOWN',exact:true}).click();await expect(page.getByRole('heading',{name:'Inspect: Controller board'})).toBeVisible();
 await page.getByLabel('Position x').fill('1.2');await page.getByLabel('Manual component correspondence').selectOption('USER_CONFIRMED');await page.getByRole('button',{name:'Save assembly revision',exact:true}).click();await expect(page.getByText('Scene changes saved as a user-confirmed engineering revision.')).toBeVisible();
 await page.getByLabel('Connection start',{exact:true}).selectOption('chassis');await page.getByLabel('Connection end',{exact:true}).selectOption('board');await page.getByRole('button',{name:'Add declared connection'}).click();await page.getByRole('button',{name:'Save connection declarations'}).click();await page.getByRole('button',{name:'Reset 3D view'}).click();await expect(page.getByTestId('robot-scene')).toHaveAttribute('data-ready','true');await page.reload();await page.getByRole('button',{name:'Controller board · USER_CONFIRMED',exact:true}).click();await expect(page.getByLabel('Position x')).toHaveValue('1.2');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBeTruthy();
});

test('synthetic MediaStream capture evidence and independent PASS boundary',async({page,context})=>{
 const root=await setup(page);await context.grantPermissions(['camera']);
 // Explicit software fixture: this release runner's headless Chromium omits native getUserMedia.
 // Canvas-generated MediaStream tests the actual video/canvas capture, stop and evidence flow.
 await page.addInitScript(()=>{Object.defineProperty(navigator.mediaDevices,'getUserMedia',{value:async()=>{
  const canvas=document.createElement('canvas');canvas.width=640;canvas.height=480;const ctx=canvas.getContext('2d')!;
  const paint=()=>{ctx.fillStyle='#27405d';ctx.fillRect(0,0,640,480);ctx.fillStyle='#ffffff';ctx.fillText('SYNTHETIC SOFTWARE TEST FRAME',30,50);};paint();
  const stream=canvas.captureStream(10);const timer=setInterval(paint,100);stream.getVideoTracks()[0].addEventListener('ended',()=>clearInterval(timer));
  Object.assign(window,{roboTestStream:stream});return stream;
 }});Object.defineProperty(navigator.mediaDevices,'enumerateDevices',{value:async()=>[]});});
 await page.goto(root+'/workspace/build');
 await expect(page.getByText('Camera not broadcasting')).toBeVisible();await page.getByRole('button',{name:'Enable camera',exact:true}).click();await expect(page.getByRole('button',{name:'Take local photo'})).toBeVisible();
 await expect.poll(async()=>page.getByLabel('Live local camera').evaluate((v:HTMLVideoElement)=>v.videoWidth)).toBeGreaterThan(0);
 await page.getByRole('button',{name:'Take local photo'}).click();await expect(page.getByAltText('Selected engineering evidence; unverified')).toBeVisible();await page.getByRole('button',{name:'Stop camera',exact:true}).click();await expect.poll(()=>page.evaluate(()=>(window as unknown as {roboTestStream:MediaStream}).roboTestStream.getTracks()[0].readyState)).toBe('ended');
 await page.getByLabel('Observation title').fill('Synthetic camera QA evidence');await page.getByLabel('Measurement / observation notes').fill('Synthetic browser feed tests capture and storage. No physical assembly was observed.');await page.getByLabel('Verification state',{exact:true}).selectOption('PASS');await expect(page.getByRole('button',{name:'Save verification evidence'})).toBeDisabled();await page.getByLabel('Verification state',{exact:true}).selectOption('REVIEW');
 await page.getByLabel('Store this image on the backend and share it with project members').check();await page.getByRole('button',{name:'Save verification evidence'}).click();await expect(page.getByText(/Observation saved\. The state is user-reported/)).toBeVisible();await page.goto(root+'/evidence');await expect(page.getByRole('heading',{name:/Synthetic camera QA evidence/})).toBeVisible();await page.getByText('View stored evidence image').click();await expect(page.getByAltText('User evidence: Synthetic camera QA evidence')).toBeVisible();
});

test('camera denial stays safe and upload evidence works',async({page})=>{
 const root=await setup(page);await page.addInitScript(()=>{Object.defineProperty(navigator.mediaDevices,'getUserMedia',{value:async()=>{throw new DOMException('Denied by test','NotAllowedError');}});});await page.goto(root+'/workspace/build');await page.getByRole('button',{name:'Enable camera',exact:true}).click();await expect(page.getByText(/Camera permission denied/)).toBeVisible();await expect(page.getByText('Camera not broadcasting')).toBeVisible();
 await page.getByLabel('Or choose an engineering image').setInputFiles('tests/fixtures/synthetic-evidence.png');await expect(page.getByAltText('Selected engineering evidence; unverified')).toBeVisible();await page.getByLabel('Observation title').fill('Uploaded software test image');await page.getByLabel('Measurement / observation notes').fill('Synthetic file upload verifies software handling only. No real assembly was observed.');await page.getByLabel('Store this image on the backend and share it with project members').check();await page.getByRole('button',{name:'Save verification evidence'}).click();await expect(page.getByText(/Observation saved\. The state is user-reported/)).toBeVisible();
});

test('authenticated simulation telemetry reaches twin and owner control remains HOLD',async({page})=>{
 const root=await setup(page);await page.goto(root+'/twin');await page.getByLabel('Device name',{exact:true}).fill('QA simulation controller');await page.getByLabel('Telemetry origin').selectOption('SIMULATION');await page.getByRole('button',{name:'Register device',exact:true}).click();await expect(page.getByText('Device token · shown once')).toBeVisible();await page.getByLabel('Simulation soil moisture (%)').fill('42');await page.getByRole('button',{name:'Send labeled simulation sample'}).click();await expect(page.getByText('soil_moisture',{exact:true})).toBeVisible();await expect(page.getByRole('cell',{name:'SIMULATION',exact:true}).first()).toBeVisible();await expect(page.getByText('42 %',{exact:false}).first()).toBeVisible();
 await page.getByLabel('Reason and safety review context').fill('Software-only request review. No physical executor is connected.');await page.getByRole('button',{name:'Request owner review'}).click();await expect(page.getByText('SAFE_STOP · PENDING')).toBeVisible();page.once('dialog',dialog=>dialog.accept());await page.getByRole('button',{name:'Approve intent, keep HOLD'}).click();await expect(page.getByText('SAFE_STOP · APPROVED_HOLD')).toBeVisible();
 await page.getByRole('button',{name:'Hide device token'}).click();await expect(page.getByText('Device token · shown once')).toHaveCount(0);
});

test('integrated pages have no serious accessibility failures and fit viewport',async({page})=>{
 const root=await setup(page);
 for(const suffix of ['/workspace/plan','/workspace/practice','/workspace/build','/twin','/evidence']){
  await page.goto(root+suffix);await expect(page.locator('main h1')).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),{message:'No horizontal overflow on '+suffix}).toBeTruthy();
  const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(results.violations.filter(v=>v.impact==='critical'||v.impact==='serious'),JSON.stringify(results.violations)).toEqual([]);
 }
});
