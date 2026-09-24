import {el,status,money,day,link,button,heading,field,selectField,formError,run,activityList,labelStatus} from "./api.js";
const sectionHead=(title,sub,action)=>el("div",{class:"section-head"},el("div",{},el("h2",{},title),sub?el("small",{},sub):null),action||null);

function quotePanel(job,a){
  const current=job.quotes.at(-1),editable=["draft","quoted"].includes(job.status),panel=el("section",{class:"panel"}),
    error=formError(),lines=el("div",{}),form=el("form",{}),save=el("button",{type:"submit",class:"button primary"},"Save quote revision"),
    approve=current?.state==="draft"&&job.status==="draft"?button("Approve saved quote",()=>run(approve,error,async()=>{
      await a.mutate(job,"quotes/"+current.id+"/approve");a.toast("Quote approved internally. Ready to schedule.");
    }),"button dark"):null;
  panel.append(sectionHead("Quote workspace","Illustrative CAD · Tax excluded",current?status(current.state==="approved"?"quoted":"draft"):null));
  panel.append(el("p",{class:"notice"},"Sample prices for demonstration only. Internal approval does not mean the customer has accepted the quote."));
  if(!editable){
    panel.append(el("div",{class:"notice green"},"This job is "+labelStatus(job.status).toLowerCase()+". Its approved quote is read-only."));
    (current?.lines||[]).forEach(l=>panel.append(el("div",{class:"revision"},el("span",{},l.description,el("small",{}," · "+l.quantity+" × "+money(l.unit_price))),el("strong",{},money(l.total)))));
    panel.append(el("div",{class:"quote-total"},el("span",{},"Approved subtotal"),el("strong",{},money(current?.total))));
  }else{
    const dirty=()=>{if(approve){approve.disabled=true;approve.textContent="Save changes before approval";}};
    const addLine=(line={description:"",quantity:"1",unit_price:"0.00"})=>{
      const row=el("div",{class:"line-grid"});
      row.append(el("input",{name:"description","aria-label":"Line description",value:line.description,required:true,maxlength:300,placeholder:"Service description"}),
        el("input",{name:"quantity","aria-label":"Quantity",type:"number",step:"0.001",min:0,max:100000,value:line.quantity,required:true}),
        el("input",{name:"unit_price","aria-label":"Unit price CAD",type:"number",step:"0.01",min:0,max:1000000,value:line.unit_price,required:true}),
        el("button",{type:"button",class:"remove-line","aria-label":"Remove line",onclick:()=>{row.remove();dirty();}},"×"));
      lines.append(row);
    };
    (current?.lines||[{description:"Illustrative site services",quantity:"1",unit_price:"1500.00"}]).forEach(addLine);
    form.append(el("div",{class:"line-grid line-head"},el("span",{},"DESCRIPTION"),el("span",{},"QUANTITY"),el("span",{},"UNIT PRICE"),el("span",{},"")),lines,
      button("＋ Add line item",()=>{if(lines.children.length<30){addLine();dirty();}else a.toast("A quote can contain up to 30 lines.");},"button small"),
      el("div",{class:"quote-total"},el("div",{},el("span",{},current?"Last saved subtotal":"Save to calculate the subtotal"),el("small",{}," · Before tax")),el("strong",{},current?money(current.total):"—")),
      error,el("div",{class:"actions"},save,approve));
    form.addEventListener("input",dirty);
    form.addEventListener("submit",e=>{e.preventDefault();run(save,error,async()=>{
      const values=[...lines.children].map(row=>Object.fromEntries([...row.querySelectorAll("input")].map(input=>[input.name,input.value])));
      await a.mutate(job,"quotes",{lines:values});a.toast("Quote revision saved. Review it before approval.");
    });});panel.append(form);
  }
  if(job.quotes.length)panel.append(el("details",{class:"section-bottom"},el("summary",{},"Quote history · "+job.quotes.length+" revision"+(job.quotes.length>1?"s":"")),
    job.quotes.slice().reverse().map(q=>el("div",{class:"revision"},el("span",{},"Revision "+q.revision+" · "+(q.state==="approved"?"Internally approved":"Draft")),el("strong",{},money(q.total))))));
  return panel;
}
function schedulingPanel(job,s,a){
  const panel=el("section",{class:"panel"},sectionHead("Crew & equipment","Whole-day reservations · Toronto time")),assignment=job.assignment;
  if(assignment)panel.append(el("div",{class:"notice green"},el("strong",{},s.crews.find(c=>c.id===assignment.crew_id)?.name+" · "+s.equipment.find(e=>e.id===assignment.equipment_id)?.name),
    el("p",{},day(assignment.start_date)+" – "+day(assignment.end_date))));
  if(!["quoted","scheduled"].includes(job.status)){
    if(job.status==="draft")panel.append(el("p",{class:"notice"},"Approve the current quote to unlock scheduling."));
    else panel.append(el("p",{class:"muted"},"Assignment locked while work is in progress or completed."));
    return panel;
  }
  const form=el("form",{}),error=formError(),save=el("button",{type:"submit",class:"button primary"},assignment?"Save new assignment":"Schedule job");
  form.append(selectField("Crew","crew_id",s.crews,assignment?.crew_id),
    selectField("Equipment","equipment_id",s.equipment,assignment?.equipment_id),
    el("div",{class:"form-grid"},field("Start date","start_date",assignment?.start_date||job.requested_start,"date",{required:true}),
      field("End date","end_date",assignment?.end_date||job.requested_end,"date",{required:true})),error,save);
  form.addEventListener("submit",e=>{e.preventDefault();run(save,error,async()=>{
    await a.mutate(job,"assignment",Object.fromEntries(new FormData(form)),"PUT");a.toast("Crew and equipment assignment saved.");
  });});panel.append(form);return panel;
}
function draftPanel(job,a){
  const error=formError(),generate=button("✧  Prepare customer update",()=>run(generate,error,async()=>{
    await a.mutate(job,"drafts");a.toast("Sample update drafted from saved job facts. Nothing was sent.");
  }),"button"),panel=el("section",{class:"panel"},sectionHead("Customer updates","Prepared from saved facts · Sample assistant"),el("p",{class:"notice"},"Review and edit before sharing. This workspace does not send email."),error,generate);
  job.drafts.slice().reverse().forEach(d=>{
    const form=el("form",{class:"draft-block"}),err=formError(),save=el("button",{class:"button primary",type:"submit"},"Save draft");
    const subject=field("Subject","subject",d.subject,"text",{required:true,maxlength:200}),
      body=field("Message","body",d.body,"textarea",{required:true,maxlength:4000,rows:8});
    const copy=button("Copy message",()=>run(copy,err,async()=>{
      const content=subject.querySelector("input").value+"\n\n"+body.querySelector("textarea").value;
      try{await navigator.clipboard.writeText(content);a.toast("Message copied. Nothing was sent.");}
      catch{body.querySelector("textarea").select();throw new Error("Clipboard access is unavailable. The message is selected so you can copy it manually.");}
    }));
    form.append(subject,body,err,el("div",{class:"actions"},save,copy));
    form.addEventListener("submit",e=>{e.preventDefault();run(save,err,async()=>{
      await a.mutate(job,"drafts/"+d.id,Object.fromEntries(new FormData(form)),"PUT");a.toast("Customer draft saved.");
    });});panel.append(form);
  });return panel;
}
export function renderJob(root,job,s,a){
  root.append(el("div",{class:"job-topline"},link("← All jobs","#jobs"),el("span",{},"/"),el("span",{},job.number),status(job.status)));
  const stateError=formError(),next={scheduled:"in_progress",in_progress:"completed"}[job.status];
  const advance=next?button(next==="in_progress"?"Start job →":"Mark completed ✓",()=>run(advance,stateError,async()=>{
    await a.mutate(job,"status",{status:next});a.toast("Job marked "+labelStatus(next).toLowerCase()+".");
  }),"button primary"):null;
  root.append(heading("PROJECT WORKSPACE",job.title,job.customer_name+" · "+job.site,advance),stateError);
  const steps=["draft","quoted","scheduled","in_progress","completed"],index=steps.indexOf(job.status);
  root.append(el("div",{class:"progress-track"},steps.map((st,i)=>el("span",{class:"progress-step "+(i===index?"current":i<index?"done":"")},String(i+1).padStart(2,"0")+"  "+labelStatus(st)))));
  const detail=el("section",{class:"panel"},sectionHead("Job details","Reviewed inquiry information"),
    el("dl",{class:"metadata"},el("div",{},el("dt",{},"Customer"),el("dd",{},job.customer_name)),
      el("div",{},el("dt",{},"Service"),el("dd",{},job.service)),
      el("div",{},el("dt",{},"Site"),el("dd",{},job.site)),
      el("div",{},el("dt",{},"Requested dates"),el("dd",{},day(job.requested_start)+" – "+day(job.requested_end))),
      el("div",{},el("dt",{},"Record version"),el("dd",{},"Version "+job.version+" · Saved in your workspace"))));
  const noteError=formError(),noteForm=el("form",{}),noteSave=el("button",{class:"button",type:"submit"},"Save note");
  noteForm.append(field("Operational note","text","","textarea",{required:true,maxlength:4000,placeholder:"Site access, customer updates, or an office handoff…",rows:3}),noteError,noteSave);
  noteForm.addEventListener("submit",e=>{e.preventDefault();run(noteSave,noteError,async()=>{await a.mutate(job,"notes",Object.fromEntries(new FormData(noteForm)));a.toast("Operational note saved.");});});
  const activity=el("section",{class:"panel"},sectionHead("Notes & activity","Changes and handoffs, in one place"),noteForm,activityList(job.activity));
  root.append(el("div",{class:"job-workspace"},el("div",{class:"stack"},quotePanel(job,a),draftPanel(job,a)),el("div",{class:"stack"},detail,schedulingPanel(job,s,a),activity)));
}
