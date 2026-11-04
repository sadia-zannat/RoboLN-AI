import {test} from 'node:test';import assert from 'node:assert/strict';
import {translateAssembly,allowedParent} from '../../lib/assembly-placement.ts';
import type {Part} from '../../lib/workbench';
const part=(id:string,parent_id:string|null,x:number,y:number,z:number):Part=>({id,parent_id,name:id,visual:'generic',kind:'other',quantity:1,specification:'provisional',source_id:null,x,y,z,state:'UNKNOWN'});
test('moving a parent translates its linked descendants without moving unrelated parts',()=>{
 const parts=[part('root',null,0,1,0),part('camera','root',1,1.7,0),part('lens','camera',2,2,0),part('unrelated',null,4,4,4)];
 const next=translateAssembly(parts,'root',1,2,3);
 assert.deepEqual(next.map(p=>[p.x,p.y,p.z]),[[1,2,3],[2,2.7,3],[3,3,3],[4,4,4]]);
 assert.equal(parts[0].x,0,'Original saved state is not mutated');
});
test('movement is bounded to backend workspace coordinate limits',()=>{
 const parts=[part('root',null,9.8,9.9,9.8),part('child','root',9.9,9.9,9.9)];
 const next=translateAssembly(parts,'root',50,50,-50);
 for(const p of next){assert.ok(p.x<=10&&p.x>=-10);assert.ok(p.y<=10&&p.y>=0);assert.ok(p.z<=10&&p.z>=-10);}
});
test('group movement preserves child offsets at every workspace boundary',()=>{
 const parts=[part('root',null,9,1,-9),part('child','root',9.9,.1,-9.9)];
 const next=translateAssembly(parts,'root',50,-50,-50);
 for(const axis of ['x','y','z'] as const){
  assert.ok(Math.abs((next[1][axis]-next[0][axis])-(parts[1][axis]-parts[0][axis]))<1e-9);
 }
 assert.equal(next[1].x,10);assert.equal(next[1].y,0);assert.equal(next[1].z,-10);
});
test('non-finite position changes do not mutate the assembly',()=>{
 const parts=[part('root',null,0,1,0)];
 for(const invalid of [NaN,Infinity,-Infinity])assert.equal(translateAssembly(parts,'root',invalid,1,0),parts);
});
test('a component cannot become its own parent or a descendant parent',()=>{
 const parts=[part('root',null,0,1,0),part('camera','root',0,2,0),part('lens','camera',0,3,0)];
 assert.equal(allowedParent(parts,'root','lens'),false);
 assert.equal(allowedParent(parts,'camera','camera'),false);
 assert.equal(allowedParent(parts,'lens','root'),true);
});
