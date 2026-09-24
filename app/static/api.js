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
const watchedForms=new WeakMap();
const formValues=form=>Array.from(form.elements).filter(control=>control.name).map(control=>[control.name,
  ["checkbox","radio"].includes(control.type)?control.checked:control.value]);
export function watchForm(form,label) {
  watchedForms.set(form,{label,before:formValues(form)});return form;
}
export function findUnsavedForms(forms,activeKey) {
  return [...new Set(forms.filter(form=>form.key!==activeKey&&JSON.stringify(form.before)!==JSON.stringify(form.after)).map(form=>form.label))];
}
function confirmDiscard(labels) {
  return new Promise(resolve=>{
    const dialog=el("dialog",{"aria-labelledby":"unsaved-title"},el("h2",{id:"unsaved-title"},"Keep your other edits?"),
      el("p",{},"You have unsaved changes in: "+labels.join(", ")+". Continuing this action will discard those other edits."));
    const finish=value=>{dialog.close();dialog.remove();resolve(value);};
    dialog.append(el("div",{class:"actions"},button("Keep editing",()=>finish(false),"button primary"),
      button("Discard other edits and continue",()=>finish(true))));
    dialog.addEventListener("cancel",event=>{event.preventDefault();finish(false);});
    document.body.append(dialog);dialog.showModal();
  });
}
let mutationPending=false;
export async function run(buttonNode,errorNode,task,protect=false) {
  if(protect&&mutationPending)return;
  if(protect)mutationPending=true;
  errorNode.replaceChildren();buttonNode.disabled=true;buttonNode.setAttribute("aria-busy","true");
  const root=document.getElementById("root");
  try{
    if(protect){
      const forms=Array.from(document.querySelectorAll("form")).filter(form=>watchedForms.has(form))
        .map(form=>({key:form,...watchedForms.get(form),after:formValues(form)}));
      const dirty=findUnsavedForms(forms,buttonNode.closest("form"));
      if(dirty.length&&!await confirmDiscard(dirty))return;
      if(root)root.inert=true;
    }
    await task();
  }catch(error){errorNode.append(el("p",{},error.message));
    if(error.status===409||error.status===401)errorNode.append(button("Reload latest data",()=>location.reload(),"button small"));
  }finally{
    if(protect){mutationPending=false;if(root)root.inert=false;}
    buttonNode.disabled=false;buttonNode.removeAttribute("aria-busy");
  }
}
export function empty(title,detail,action=null) {
  return el("div",{class:"empty"},el("span",{class:"empty-icon","aria-hidden":"true"},"◇"),el("h3",{},title),el("p",{},detail),action);
}
export function activityWindow(events,limit=8) {
  const newest=events.slice().reverse();return limit===null?newest:newest.slice(0,limit);
}
export function activityList(events,jobs=[],expandable=false) {
  let expanded=false;
  const rows=el("div",{class:"activity-list"});
  const render=()=>rows.replaceChildren(...(events.length?activityWindow(events,expanded?null:8).map(item=>
    el("div",{class:"activity"},el("span",{class:"activity-dot kind-"+item.kind}),el("div",{},el("p",{},item.text),el("small",{},
      jobs.find(j=>j.id===item.job_id)?.number||"Workspace"," · ",new Date(item.created_at).toLocaleString("en-CA",{month:"short",day:"numeric",hour:"numeric",minute:"2-digit",timeZone:"America/Toronto"}))))):[el("p",{class:"muted"},"Your next action will appear here.")]));
  render();
  if(!expandable||events.length<=8)return rows;
  const toggle=button("Show all activity ("+events.length+")",()=>{
    expanded=!expanded;render();toggle.textContent=expanded?"Show recent activity":"Show all activity ("+events.length+")";
    toggle.setAttribute("aria-expanded",String(expanded));
  },"button small");
  toggle.setAttribute("aria-expanded","false");return el("div",{},rows,toggle);
}
