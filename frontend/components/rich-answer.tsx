import type {ReactNode} from 'react';

// Display provider-supplied Markdown as safe React elements. This renderer intentionally
// does not interpret HTML or execute links/scripts from untrusted model output.
function inline(text:string,key:string):ReactNode[] {
 const tokens=text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`|\[[^\]\n]+\]\(https?:\/\/[^\s)]+\))/g);
 return tokens.map((token,i)=>{
  if(token.startsWith('**')&&token.endsWith('**'))return <strong key={key+'b'+i}>{token.slice(2,-2)}</strong>;
  if(token.startsWith('`')&&token.endsWith('`'))return <code key={key+'c'+i}>{token.slice(1,-1)}</code>;
  const link=/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/.exec(token);
  if(link){try{const url=new URL(link[2]);if(['https:','http:'].includes(url.protocol))return <a key={key+'a'+i} href={url.href} target="_blank" rel="noopener noreferrer">{link[1]}</a>;}catch{}}
  return token;
 });
}
export function RichAnswer({text}:{text:string}){
 const rows=text.replace(/\r\n/g,'\n').split('\n');const nodes:ReactNode[]=[];
 let i=0;
 while(i<rows.length){
  const line=rows[i],trim=line.trim();if(!trim){i++;continue;}
  if(/^```/.test(trim)){
   const language=trim.slice(3).trim();const code:string[]=[];i++;
   while(i<rows.length&&!/^```/.test(rows[i].trim()))code.push(rows[i++]);
   if(i<rows.length)i++;
   nodes.push(<div className="answer-code" key={'code'+i}>{language&&<span>{language}</span>}<pre><code>{code.join('\n')}</code></pre></div>);continue;
  }
  const heading=/^(#{1,4})\s+(.+)$/.exec(trim);
  if(heading){nodes.push(<h3 className="answer-heading" key={'h'+i}>{inline(heading[2],'h'+i)}</h3>);i++;continue;}
  if(/^([-*_]\s*){3,}$/.test(trim)){nodes.push(<hr key={'hr'+i}/>);i++;continue;}
  if(/^\s*\|.+\|\s*$/.test(line)){
   const lines:string[]=[];while(i<rows.length&&/^\s*\|.+\|\s*$/.test(rows[i]))lines.push(rows[i++]);
   const cells=lines.map(r=>r.trim().replace(/^\||\|$/g,'').split('|').map(x=>x.trim()));
   const filtered=cells.filter(row=>!row.every(x=>/^:?-{2,}:?$/.test(x)));
   nodes.push(<div className="answer-table-scroll" key={'t'+i}><table><tbody>{filtered.map((row,j)=><tr key={j}>{row.map((c,k)=>j===0?<th key={k}>{inline(c,'th'+i+k)}</th>:<td key={k}>{inline(c,'td'+i+j+k)}</td>)}</tr>)}</tbody></table></div>);continue;
  }
  const bullet=/^\s*([-*+]\s+|\d+[.)]\s+)(.*)$/.exec(line);
  if(bullet){const numbered=/^\s*\d+[.)]\s+/.test(line);const items:string[]=[];
   while(i<rows.length){const m=/^\s*([-*+]\s+|\d+[.)]\s+)(.*)$/.exec(rows[i]);if(!m||/^\s*\d+[.)]\s+/.test(rows[i])!==numbered)break;items.push(m[2]);i++;}
   const listItems=items.map((s,j)=><li key={j}>{inline(s,'li'+i+j)}</li>);
   nodes.push(numbered?<ol key={'ol'+i}>{listItems}</ol>:<ul key={'ul'+i}>{listItems}</ul>);continue;
  }
  if(/^>\s?/.test(trim)){nodes.push(<blockquote key={'q'+i}>{inline(trim.replace(/^>\s?/,''),'q'+i)}</blockquote>);i++;continue;}
  const paragraph:string[]=[trim];i++;
  while(i<rows.length&&rows[i].trim()&&!/^(#{1,4}\s+|```|\s*[-*+]\s+|\s*\d+[.)]\s+|\s*\|.+\|\s*$|>\s?)/.test(rows[i]))paragraph.push(rows[i++].trim());
  nodes.push(<p key={'p'+i}>{inline(paragraph.join(' '),'p'+i)}</p>);
 }
 return <div className="rich-answer">{nodes.length?nodes:<p>No answer text returned.</p>}</div>;
}
