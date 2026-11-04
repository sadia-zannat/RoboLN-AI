export const projectUrl=(id:string,where:'detail'|'plan'|'practice'|'build'|'twin'|'evidence'|'copilot'='detail')=>{
  const root='/projects/'+encodeURIComponent(id);
  return where==='detail'?root:where==='twin'||where==='evidence'?root+'/'+where:root+'/workspace/'+where;
};
export function logicalParent(path:string):string {
  if(path.includes('/workspace/copilot'))return path.replace('/workspace/copilot','/workspace/plan');
  if(path.includes('/workspace/build'))return path.replace('/workspace/build','/workspace/practice');
  if(path.includes('/workspace/practice'))return path.replace('/workspace/practice','/workspace/plan');
  if(path.includes('/workspace/plan')||path.endsWith('/twin')||path.endsWith('/evidence'))return path.split('/').slice(0,3).join('/');
  return '/projects';
}
export const projectIdFromPath=(path:string)=>{
  const m=path.match(/^\/projects\/([^/]+)/);
  if(!m)return null;
  try {return decodeURIComponent(m[1]);}
  catch {return null;} // malformed deep-link encoding must not crash navigation
};
