// Runs the actual pure frontend navigation helpers via installed TypeScript.
// This is NOT a Next.js rendering or Playwright browser test.
const ts=require(process.env.ROBOLN_GLOBAL_TS||'../frontend/node_modules/typescript');
const fs=require('fs');const path=require('path');const vm=require('vm');const assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../frontend/lib/navigation.ts'),'utf8');
const output=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const navExports={};vm.runInNewContext(output,{exports:navExports,encodeURIComponent,decodeURIComponent});
let checked=0;const check=(actual,expected)=>{assert.equal(actual,expected);checked++;};
const id='safe-project-01';
check(navExports.projectUrl(id),'/projects/safe-project-01');
check(navExports.projectUrl(id,'plan'),'/projects/safe-project-01/workspace/plan');
check(navExports.projectUrl(id,'practice'),'/projects/safe-project-01/workspace/practice');
check(navExports.projectUrl(id,'build'),'/projects/safe-project-01/workspace/build');
check(navExports.projectUrl(id,'twin'),'/projects/safe-project-01/twin');
check(navExports.projectUrl(id,'evidence'),'/projects/safe-project-01/evidence');
check(navExports.projectUrl('user/id','plan'),'/projects/user%2Fid/workspace/plan');
check(navExports.logicalParent('/projects/abc/workspace/build'),'/projects/abc/workspace/practice');
check(navExports.logicalParent('/projects/abc/workspace/practice'),'/projects/abc/workspace/plan');
check(navExports.logicalParent('/projects/abc/workspace/plan'),'/projects/abc');
check(navExports.logicalParent('/projects/abc/twin'),'/projects/abc');
check(navExports.logicalParent('/projects/abc/evidence'),'/projects/abc');
check(navExports.logicalParent('/settings'),'/projects');
check(navExports.projectIdFromPath('/projects/my-project/twin'),'my-project');
check(navExports.projectIdFromPath('/projects/abc%20def/workspace/plan'),'abc def');
check(navExports.projectIdFromPath('/projects/%E0%A4%A'),null);
check(navExports.projectIdFromPath('/projects'),null);
console.log(`PASS: ${checked} pure navigation assertions from actual TS source. This is NOT browser E2E.`);
