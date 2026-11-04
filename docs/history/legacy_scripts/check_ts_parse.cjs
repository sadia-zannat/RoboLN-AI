// This checks only TS/TSX syntax, NOT typecheck or bundling.
const fs=require('fs'),path=require('path');
const ts=require(process.env.ROBOLN_GLOBAL_TS||'/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript');
const root=path.join(__dirname,'..','frontend');let files=[],errors=[];
function walk(p){for(const d of fs.readdirSync(p,{withFileTypes:true})){const f=path.join(p,d.name);if(d.isDirectory() && d.name!=='node_modules' && d.name!=='.next')walk(f);else if(d.isFile() && /\.tsx?$/.test(f))files.push(f);}}
walk(root);for(const f of files){const sf=ts.createSourceFile(f,fs.readFileSync(f,'utf8'),ts.ScriptTarget.Latest,true,f.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS);for(const e of sf.parseDiagnostics)errors.push(f+': '+ts.flattenDiagnosticMessageText(e.messageText,' '));}
console.log('TS/TSX syntax-only parse:',files.length,'files;',errors.length,'parse errors');errors.forEach(x=>console.error(x));if(errors.length)process.exit(1);
