export async function api(path, options = {}) {
  let response;
  try { response = await fetch(path, {...options, credentials:"same-origin",headers:{"Content-Type":"application/json",...(options.headers||{})}}); }
  catch { throw new Error("Could not reach the workspace. Check the local server, then try again."); }
  let payload;
  try { payload=await response.json(); } catch { throw new Error("The server returned an unexpected response. Try reloading."); }
  if(!response.ok) {
    const detail=typeof payload.detail==="string" ? payload.detail : (payload.detail||[]).map(item=>item.loc?.slice(1).join(".")+": "+item.msg).join("; ");
    const error=new Error(detail||"The action could not be completed."); error.status=response.status; throw error;
  }
  return payload;
}
export function el(tag,attrs={},...children) {
  const node=document.createElement(tag);
  for(const [key,value] of Object.entries(attrs)) {
    if(value==null||value===false) continue;
    if(key.startsWith("on")) node.addEventListener(key.slice(2),value);
    else if(key==="class") node.className=value;
    else if(key==="value") node.value=value;
    else node.setAttribute(key,value===true?"":value);
  }
  for(const child of children.flat(Infinity)) if(child!==null&&child!==undefined&&child!==false)
    node.append(child instanceof Node?child:document.createTextNode(String(child)));
  return node;
}
export const labelStatus=s=>({draft:"Draft",quoted:"Quote approved",scheduled:"Scheduled",in_progress:"In progress",completed:"Completed"}[s]||s);
export const status=s=>el("span",{class:"status status-"+s},el("span",{class:"status-dot"}),labelStatus(s));
export const money=value=>new Intl.NumberFormat("en-CA",{style:"currency",currency:"CAD",maximumFractionDigits:2}).format(Number(value||0));
export const day=value=>value?new Intl.DateTimeFormat("en-CA",{month:"short",day:"numeric",timeZone:"UTC"}).format(new Date(value+"T12:00:00Z")):"Not scheduled";
export const addDays=(value,count)=>{const d=new Date(value+"T12:00:00Z");d.setUTCDate(d.getUTCDate()+count);return d.toISOString().slice(0,10);};
export const link=(text,href,cls="text-link")=>el("a",{href,class:cls},text);
export const button=(text,action,cls="button")=>el("button",{type:"button",class:cls,onclick:action},text);
export function heading(eyebrow,title,description,action) {
  return el("div",{class:"page-heading"},el("div",{},el("span",{class:"eyebrow"},eyebrow),el("h1",{},title),el("p",{},description)),action||null);
}
export function field(label,name,value="",type="text",options={}) {
  const control=type==="textarea"?el("textarea",{name,rows:options.rows||4,...options}):el("input",{name,type,...options});
  control.value=value??"";return el("label",{class:"field"},el("span",{},label),control);
}
export function selectField(label,name,values,selected="") {
  const select=el("select",{name},values.map(v=>el("option",{value:v.id},v.name)));
  if(selected)select.value=selected;return el("label",{class:"field"},el("span",{},label),select);
}
export const formError=()=>el("div",{class:"form-error",role:"alert"});
export async function run(buttonNode,errorNode,task) {
  errorNode.replaceChildren();buttonNode.disabled=true;buttonNode.setAttribute("aria-busy","true");
  try{await task();}catch(error){errorNode.append(el("p",{},error.message));
    if(error.status===409||error.status===401)errorNode.append(button("Reload latest data",()=>location.reload(),"button small"));
  }finally{buttonNode.disabled=false;buttonNode.removeAttribute("aria-busy");}
}
export function empty(title,detail,action=null) {
  return el("div",{class:"empty"},el("span",{class:"empty-icon","aria-hidden":"true"},"◇"),el("h3",{},title),el("p",{},detail),action);
}
export function activityList(events,jobs=[]) {
  return el("div",{class:"activity-list"},events.length?events.slice().reverse().slice(0,8).map(item=>
    el("div",{class:"activity"},el("span",{class:"activity-dot kind-"+item.kind}),el("div",{},el("p",{},item.text),el("small",{},
      jobs.find(j=>j.id===item.job_id)?.number||"Workspace"," · ",new Date(item.created_at).toLocaleTimeString("en-CA",{hour:"numeric",minute:"2-digit",timeZone:"America/Toronto"}))))):el("p",{class:"muted"},"Your next action will appear here."));
}
