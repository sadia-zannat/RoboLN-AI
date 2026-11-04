'use client';
import {useEffect,useRef,useState} from 'react';
import {Camera,CameraOff,RefreshCcw,ShieldCheck,Video} from 'lucide-react';

/** Local preview; captured images leave this component only through an explicit parent workflow. */
export function LocalCamera({onCapture,compact=false}:{onCapture?:(photo:string|null)=>void;compact?:boolean}){
 const video=useRef<HTMLVideoElement>(null);
 const active=useRef<MediaStream|null>(null);
 const pending=useRef(0);
 const mounted=useRef(true);
 const [status,setStatus]=useState<'OFF'|'REQUESTING'|'ACTIVE'|'DENIED'|'ERROR'>('OFF');
 const [message,setMessage]=useState('The camera is off. Enable it only when you are ready.');
 const [photo,setPhoto]=useState<string|null>(null);
 const [devices,setDevices]=useState<MediaDeviceInfo[]>([]);
 const [deviceId,setDeviceId]=useState('');
 const stop=()=>{
  pending.current++;
  active.current?.getTracks().forEach(track=>track.stop());
  active.current=null;
  if(video.current){video.current.pause();video.current.srcObject=null;}
  if(mounted.current){setStatus('OFF');setMessage('Camera stopped. Live preview has ended.');}
 };
 useEffect(()=>{
  // Capture the stable ref objects within this effect. Cleanup invalidates
  // any pending permission request and stops the currently owned stream.
  const mountedRef=mounted;
  const pendingRef=pending;
  const streamRef=active;
  mountedRef.current=true;
  return()=>{
   mountedRef.current=false;
   pendingRef.current+=1;
   const stream=streamRef.current;
   streamRef.current=null;
   stream?.getTracks().forEach(track=>track.stop());
  };
 },[]);
 async function start(source?:string){
  if(typeof window==='undefined'||!window.isSecureContext||!navigator.mediaDevices?.getUserMedia){
   setStatus('ERROR');setMessage('Live camera requires localhost or HTTPS and a browser with media permissions.');return;
  }
  stop();setPhoto(null);onCapture?.(null);setStatus('REQUESTING');setMessage('Waiting for browser camera permission…');
  const ticket=++pending.current;
  try{
   const choice=source||deviceId;
   const stream=await navigator.mediaDevices.getUserMedia({audio:false,video:choice?{deviceId:{exact:choice}}:{facingMode:{ideal:'environment'}}});
   if(ticket!==pending.current||!mounted.current){stream.getTracks().forEach(t=>t.stop());return;}
   active.current=stream;
   const track=stream.getVideoTracks()[0];
   track.addEventListener('ended',()=>{if(active.current===stream)stop();},{once:true});
   if(video.current){video.current.srcObject=stream;await video.current.play().catch(()=>{});}
   if(ticket!==pending.current)return;
   setStatus('ACTIVE');setMessage('Live preview stays on this device. Captured images require separate transmission or storage consent.');
   const list=await navigator.mediaDevices.enumerateDevices().catch(()=>[] as MediaDeviceInfo[]);
   if(mounted.current)setDevices(list.filter(d=>d.kind==='videoinput'));
  }catch(e){
   if(ticket!==pending.current||!mounted.current)return;
   const err=e as DOMException;
   setStatus(err.name==='NotAllowedError'?'DENIED':'ERROR');
   setMessage(err.name==='NotAllowedError'?'Camera permission denied. Enable it in the browser to retry.':err.name==='NotFoundError'?'No camera detected. Connect a camera and retry.':err.name==='NotSupportedError'?'This browser does not support camera capture. Use a supported browser or upload an image.':'Unable to start camera. Check whether another application is using it.');
  }
 }
 function capture(){
  const v=video.current;
  if(status!=='ACTIVE'||!v||!v.videoWidth||!v.videoHeight)return;
  const canvas=document.createElement('canvas');
  canvas.width=Math.min(v.videoWidth,1600);
  canvas.height=Math.round(canvas.width*v.videoHeight/v.videoWidth);
  const ctx=canvas.getContext('2d');if(!ctx)return;
  ctx.drawImage(v,0,0,canvas.width,canvas.height);
  const data=canvas.toDataURL('image/jpeg',0.78);setPhoto(data);onCapture?.(data);
  setMessage('Photo captured locally. No image has been analyzed, saved to the server, or verified.');
 }
 function savePhoto(){
  if(!photo)return;
  const a=document.createElement('a');a.href=photo;a.download='RoboLN-local-capture.jpg';a.click();
 }
 return <section className="local-camera" aria-label="Private physical camera preview">
  <div className="camera-preview">
   <video ref={video} autoPlay playsInline muted aria-label="Live local camera" style={{display:status==='ACTIVE'?'block':'none'}}/>
   {status!=='ACTIVE'&&<div className="camera-empty"><CameraOff size={32}/><strong>Camera not broadcasting</strong><span>No media is being collected.</span></div>}
  </div>
  <div className="camera-controls">
   {status==='ACTIVE'?<><button type="button" className="button secondary" onClick={capture}><Camera size={17}/>{compact?'Capture Snapshot':'Take local photo'}</button><button type="button" className="button primary" onClick={stop}><CameraOff size={17}/>Stop camera</button>{compact&&devices.length>1&&<button type="button" className="button secondary" onClick={()=>{const next=devices[(devices.findIndex(d=>d.deviceId===deviceId)+1)%devices.length].deviceId;setDeviceId(next);void start(next);}}>Switch camera</button>}</>
    :<button type="button" className="button primary" disabled={status==='REQUESTING'} onClick={()=>void start()}><Video size={17}/>{status==='REQUESTING'?'Requesting permission…':compact?'Open Camera':'Enable camera'}</button>}
   {devices.length>1&&status==='OFF'&&<label>Camera<select aria-label="Camera source" value={deviceId} onChange={e=>setDeviceId(e.target.value)}><option value="">Default camera</option>{devices.map(d=><option key={d.deviceId} value={d.deviceId}>{d.label||'Available camera'}</option>)}</select></label>}
  </div>
  <p role="status" className="camera-status"><ShieldCheck size={16}/>{message}</p>
  {photo&&<div className="local-photo"><h3>Local captured photo · NOT VERIFIED</h3>
  {/* eslint-disable-next-line @next/next/no-img-element -- local canvas data URL; no remote asset to optimize */}
  <img src={photo} alt="Photo captured locally from your camera; not machine analyzed"/>
  <div className="button-row"><button type="button" className="button secondary" onClick={savePhoto}>Save photo to this device</button><button type="button" className="button secondary" onClick={()=>{setPhoto(null);onCapture?.(null);}}><RefreshCcw size={16}/>Discard photo</button></div></div>}
 </section>;
}
