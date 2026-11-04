import {test} from 'node:test';import assert from 'node:assert/strict';
import {speechText,validatePhoto,statusLabel,proposalSteps} from '../../lib/copilot.ts';
import {transformAssembly,emptyHistory,recordEdit,undoEdit,redoEdit} from '../../lib/assembly-transform.ts';
import {isAssemblyVisible} from '../../lib/assembly-placement.ts';
import type {Part,WorkspaceData} from '../../lib/workbench';
const part=(id:string,parent_id:string|null,x:number,y=1,z=0):Part=>({id,parent_id,name:id,kind:'other',quantity:1,specification:'',source_id:null,x,y,z,rx:0,ry:0,rz:0,state:'UNKNOWN'});
const data=(parts:Part[]):WorkspaceData=>({requirements:'',constraints:'',software_notes:'',parts,tasks:[],pins:[],connections:[]});
test('parent rotation preserves offsets and moves nested descendants around the parent pivot',()=>{
 const original=[part('root',null,1),part('child','root',2),part('grandchild','child',3),part('unrelated',null,8)];
 const next=transformAssembly(original,'root',{ry:90});
 assert.ok(Math.abs(next[1].x-1)<1e-8);assert.ok(Math.abs(next[1].z+1)<1e-8);
 assert.ok(Math.abs(next[2].x-1)<1e-8);assert.ok(Math.abs(next[2].z+2)<1e-8);
 assert.equal(next[3],original[3]);assert.equal(original[1].x,2);
 const inverse=transformAssembly(next,'root',{ry:0});assert.ok(Math.abs(inverse[2].x-3)<1e-8);assert.ok(Math.abs(inverse[2].z)<1e-8);
});
test('invalid or out-of-bounds group rotations leave the entire saved draft intact',()=>{
 const parts=[part('root',null,9),part('child','root',9,1,-2)];
 assert.equal(transformAssembly(parts,'root',{ry:-90}),parts);
 assert.equal(transformAssembly(parts,'root',{rx:NaN}),parts);
 assert.equal(transformAssembly(parts,'root',{rx:Infinity}),parts);
});
test('reparenting preserves existing world placement and hidden parents hide descendants',()=>{
 const parts=[part('root',null,0),part('child',null,1)];const next=transformAssembly(parts,'child',{parent_id:'root'});
 assert.equal(next[1].x,1);assert.equal(next[1].parent_id,'root');
 assert.equal(isAssemblyVisible([{...next[0],visible:false},next[1]],'child'),false);
 assert.equal(isAssemblyVisible(next,'child'),true);
});
test('undo redo restore hierarchy and transforms; a new edit discards the old redo branch',()=>{
 const first=data([part('a',null,1)]),second=data([part('a',null,2)]),third=data([part('a',null,3)]);
 const history=recordEdit(emptyHistory(),first);const undone=undoEdit(history,second)!;assert.equal(undone.data,first);
 assert.equal(redoEdit(undone.history,first)!.data,second);
 const branched=recordEdit(undone.history,first);assert.equal(redoEdit(branched,third),null);
});
test('English speech text keeps readable instructions and does not speak code or Markdown markup',()=>{
 assert.equal(speechText('## Step\n**Place** the [camera](https://example.com).\n```python\nDO_NOT_SPEAK()\n```'),'Step Place the camera. Code is available in the written instructions.');
 assert.equal(statusLabel('NEEDS_MORE_EVIDENCE'),'Needs more evidence');
});
test('photo validation accepts bounded real image types and rejects oversized or unsupported uploads',()=>{
 assert.equal(validatePhoto({type:'image/png',size:123}),null);
 assert.match(validatePhoto({type:'text/html',size:123})!,/PNG/);
 assert.match(validatePhoto({type:'image/jpeg',size:3*1024*1024+1})!,/3 MiB/);
});

test('saved provider proposals normalize optional fields before reopening without losing evidence requirements',()=>{
 const answer=JSON.stringify({steps:[{objective:'Read labels',instruction:'Read the physical label.',evidence_required:'true'}]});
 const result=proposalSteps(answer)!;assert.deepEqual(result[0].checks,[]);assert.deepEqual(result[0].component_ids,[]);assert.equal(result[0].evidence_required,true);
 assert.equal(proposalSteps('not a JSON plan'),null);assert.equal(proposalSteps(JSON.stringify({steps:[{objective:'Bad',instruction:'Bad',checks:[42]}]})),null);
});
