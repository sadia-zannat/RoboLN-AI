import {defineConfig,devices} from '@playwright/test';
const extraArgs=process.env.ROBOLN_BROWSER_ARGS?JSON.parse(process.env.ROBOLN_BROWSER_ARGS) as string[]:[];
export default defineConfig({
 testDir:'./tests/e2e',testIgnore:['**/*.mock.spec.ts'],timeout:60000,globalTimeout:15*60*1000,expect:{timeout:10000},retries:0,workers:1,forbidOnly:!!process.env.CI,
 reporter:[['list'],['json',{outputFile:'../verification/playwright-results.json'}],['html',{outputFolder:'../logs/playwright-report',open:'never'}]],
 use:{baseURL:'http://127.0.0.1:3000',trace:'retain-on-failure',screenshot:'only-on-failure',
 launchOptions:{executablePath:process.env.ROBOLN_CHROMIUM_EXECUTABLE||undefined,args:[...extraArgs,'--use-fake-device-for-media-stream','--enable-unsafe-swiftshader']}},
 projects:[
 {name:'desktop-1440',use:{...devices['Desktop Chrome'],viewport:{width:1440,height:900}}},
 {name:'tablet-768',use:{...devices['Desktop Chrome'],viewport:{width:768,height:1024}}},
 {name:'mobile-390',use:{...devices['Desktop Chrome'],viewport:{width:390,height:844},isMobile:true,hasTouch:true}},
 {name:'mobile-320',use:{...devices['Desktop Chrome'],viewport:{width:320,height:700},isMobile:true,hasTouch:true}}
 ],
 webServer:[
 {command:'python -m alembic upgrade head && python -m uvicorn app.api:app --host 127.0.0.1 --port 8000',cwd:'../backend',env:{MODEL_API_KEY:''},url:'http://127.0.0.1:8000/api/ready',reuseExistingServer:!process.env.CI,timeout:60000},
 {command:process.env.ROBOLN_E2E_DEV==='1'?'npm run dev':'npm run start',cwd:'.',url:'http://127.0.0.1:3000/login',reuseExistingServer:!process.env.CI,timeout:90000}
 ]
});
