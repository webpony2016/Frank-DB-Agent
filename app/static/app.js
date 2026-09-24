import {api,el,run,empty} from "./api.js";
import {renderView} from "./views.js";
import {renderJob} from "./job.js";
const root=document.querySelector("#root");
let state=null,renderToken=0,toastTimer;
function toast(message){const node=document.querySelector("#toast");node.textContent=message;node.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{node.hidden=true;},4000);}
const actions={toast,go:route=>{location.hash=route;},refresh,sync:async()=>{state=await api("/api/bootstrap");},job:async id=>api("/api/jobs/"+id),
  mutate:async(job,suffix,body={},method="POST")=>{
    const updated=await api("/api/jobs/"+job.id+"/"+suffix,{method,body:JSON.stringify({...body,expected_version:job.version})});
    await refresh();return updated;
  }
};
async function refresh(){state=await api("/api/bootstrap");document.querySelector("#inbox-count").textContent=state.metrics.inquiries;await render();}
async function render(){
  const token=++renderToken,[page,id]=(location.hash.slice(1)||"overview").split("/");
  document.querySelectorAll("[data-nav]").forEach(node=>{if(node.dataset.nav===page)node.setAttribute("aria-current","page");else node.removeAttribute("aria-current");});
  document.querySelector("#page-label").textContent=({overview:"Overview",inbox:"Inbox",jobs:"Jobs",schedule:"Schedule",integrations:"Integrations"}[page]||"Workspace");
  try{
    if(page==="jobs"&&id){
      const job=await api("/api/jobs/"+encodeURIComponent(id));if(token!==renderToken)return;
      root.replaceChildren();renderJob(root,job,state,actions);
    }else{
      const integration=page==="integrations"?await api("/api/integrations"):null;if(token!==renderToken)return;
      root.replaceChildren();renderView(root,{...state,page,integration},actions);
    }
  }catch(error){if(token!==renderToken)return;root.replaceChildren(empty("Workspace unavailable",error.message,el("button",{class:"button primary",onclick:start},"Try again")));}
}
async function start(){try{await refresh();}catch(error){root.replaceChildren(empty("Let's reconnect",error.message,el("button",{class:"button primary",onclick:start},"Try again")));}}
window.addEventListener("hashchange",()=>{if(state)render().then(()=>window.scrollTo(0,0));});
const guide=document.querySelector("#guide"),reset=document.querySelector("#reset-dialog");
document.querySelector("#guide-button").addEventListener("click",()=>guide.showModal());
document.querySelector("#reset-button").addEventListener("click",()=>reset.showModal());
document.querySelector("#reset-cancel").addEventListener("click",()=>reset.close());
document.querySelector("#reset-confirm").addEventListener("click",event=>run(event.currentTarget,reset.querySelector(".form-error"),async()=>{
  await api("/api/reset",{method:"POST",body:JSON.stringify({confirm:true})});reset.close();location.hash="overview";await refresh();toast("Your sample workspace has been reset.");
}));
start();

document.querySelector(".skip").addEventListener("click",event=>{event.preventDefault();document.querySelector("#main").focus();});
