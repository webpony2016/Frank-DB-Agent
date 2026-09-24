import {api,el,status,money,day,addDays,link,button,heading,field,selectField,formError,run,empty,activityList,labelStatus} from "./api.js";

const sectionHead=(title,sub,action)=>el("div",{class:"section-head"},el("div",{},el("h2",{},title),sub?el("small",{},sub):null),action||null);
function overview(root,s,a){
  root.append(heading("YOUR OPERATIONS, CONNECTED","Good work starts with a clear plan.","Keep the office and field moving in the same direction.",link("Review inquiries →","#inbox","button primary")));
  root.append(el("div",{class:"welcome-strip"},el("span",{class:"strip-icon","aria-hidden":"true"},"↗"),el("div",{},el("strong",{},"One workspace. From inquiry to completion."),el("p",{},"Try a complete workflow with sample projects, reviewed quotes and conflict-aware scheduling.")),link("Start the walkthrough","#inbox")));
  const metrics=[["Active jobs",s.metrics.active_jobs,"Across your job pipeline","▤"],["Awaiting review",s.metrics.inquiries,"Customer inquiries in your inbox","▱"],["Draft quote value",money(s.metrics.draft_quote_value),"Illustrative CAD · Tax excluded","＄"],["Upcoming assignments",s.metrics.upcoming,"Scheduled or underway","▦"]];
  root.append(el("div",{class:"stats"},metrics.map(([title,value,caption,icon])=>el("div",{class:"stat"},el("div",{class:"stat-label"},title,el("span",{class:"stat-symbol","aria-hidden":"true"},icon)),el("div",{class:"stat-value"},value),el("div",{class:"stat-foot"},el("b",{},"●"),caption)))));
  const upcoming=s.assignments.filter(x=>x.end_date>=s.business_date&&s.jobs.find(j=>j.id===x.job_id)?.status!=="completed").sort((x,y)=>x.start_date.localeCompare(y.start_date));
  const schedule=el("section",{class:"panel"},sectionHead("Coming up on site","Toronto business dates · All-day assignments",link("View schedule ↗","#schedule")));
  upcoming.forEach(x=>{
    const j=s.jobs.find(j=>j.id===x.job_id),crew=s.crews.find(c=>c.id===x.crew_id),equipment=s.equipment.find(e=>e.id===x.equipment_id);
    schedule.append(el("a",{href:"#jobs/"+j.id,class:"job-row"},el("div",{class:"date-tile"},el("span",{},day(x.start_date).split(" ")[0]),el("strong",{},Number(x.start_date.slice(-2)))),el("div",{class:"job-row-main"},el("h3",{},j.title),el("p",{},crew.name+" · "+equipment.name+" · "+day(x.start_date)+"–"+day(x.end_date))),status(j.status),el("span",{class:"row-arrow"},"↗")));
  });
  if(!upcoming.length)schedule.append(empty("A clear schedule","Approve a quote to assign the next job."));
  const attention=el("section",{class:"panel"},sectionHead("Needs your attention","A short list to keep work moving"));
  const unconverted=s.inquiries.filter(i=>!i.job_id);
  unconverted.slice(0,2).forEach(i=>attention.append(el("div",{class:"attention-item"},el("span",{class:"attention-icon"},"▱"),el("div",{},el("strong",{},i.subject.replace("Quote request — ","")),el("p",{},"New inquiry · Ready for a reviewed job brief"),link("Review inquiry →","#inbox")))));
  s.jobs.filter(j=>j.status==="draft").slice(0,2).forEach(j=>attention.append(el("div",{class:"attention-item"},el("span",{class:"attention-icon"},"▤"),el("div",{},el("strong",{},j.title),el("p",{},"Draft quote · Internal review required"),link("Open job →","#jobs/"+j.id)))));
  if(!unconverted.length&&!s.jobs.some(j=>j.status==="draft"))attention.append(empty("All caught up","No inquiries or quotes are waiting for review."));
  const recent=el("section",{class:"panel"},sectionHead("Workspace activity","A record of what changed"),activityList(s.activity,s.jobs));
  const pipeline=el("section",{class:"panel"},sectionHead("Your job pipeline","From first draft to finished work"));
  ["draft","quoted","scheduled","in_progress","completed"].forEach(st=>pipeline.append(el("div",{class:"revision"},status(st),el("strong",{},s.jobs.filter(j=>j.status===st).length+" jobs"))));
  root.append(el("div",{class:"two-col"},el("div",{class:"stack"},schedule,recent),el("div",{class:"stack"},attention,pipeline)));
}
function inbox(root,s,a){
  root.append(heading("CUSTOMER INTAKE","Turn inquiries into a plan.","Review a sample inquiry, prepare a job brief and fill in the details."));
  const list=el("div",{class:"inquiry-list"}),detail=el("section",{class:"panel"});
  function show(i){
    list.querySelectorAll("button").forEach(b=>b.classList.toggle("active",b.dataset.id===i.id));
    const customer=s.customers.find(c=>c.id===i.customer_id),error=formError();
    detail.replaceChildren(el("div",{class:"email-heading"},el("span",{class:"eyebrow"},"SAMPLE CUSTOMER EMAIL"),el("h2",{},i.subject),el("p",{},customer.contact+" · "+customer.email)),
      el("div",{class:"email-body"},i.body),el("p",{class:"notice"},"Prepared example · The sample assistant suggests a brief for your review. No live AI request is made."),error);
    if(i.job_id){detail.append(link("Open existing job →","#jobs/"+i.job_id,"button primary"));return;}
    const prepare=button("✧  Prepare job brief",()=>run(prepare,error,async()=>{
      const result=await api("/api/inquiries/"+i.id+"/brief",{method:"POST"});prepare.remove();
      const b=result.brief,brief=el("div",{class:"brief"},sectionHead("Review the job brief","Check the sample details before creating a job.")),
        form=el("form",{}),saveError=formError(),save=el("button",{class:"button primary",type:"submit"},"Create draft job →");
      form.append(selectField("Customer","customer_id",s.customers.map(c=>({id:c.id,name:c.name})),b.customer_id),
        field("Project title","title",b.title,"text",{required:true,maxlength:200}),
        field("Site / location","site",b.site,"text",{required:true,maxlength:200}),
        field("Service category","service",b.service,"text",{required:true,maxlength:200}),
        el("div",{class:"form-grid"},field("Requested start","requested_start",b.requested_start,"date",{required:true}),field("Requested end","requested_end",b.requested_end,"date",{required:true})));
      if(b.missing_information.length)form.append(el("div",{class:"notice"},el("strong",{},"Before finalizing"),el("ul",{},b.missing_information.map(t=>el("li",{},t)))));
      form.append(saveError,save);
      form.addEventListener("submit",e=>{e.preventDefault();run(save,saveError,async()=>{
        const job=await api("/api/inquiries/"+i.id+"/job",{method:"POST",body:JSON.stringify(Object.fromEntries(new FormData(form)))});
        await a.refresh();a.go("jobs/"+job.id);a.toast("Job brief reviewed. Your draft job is ready.");
      });});
      brief.append(form);detail.append(brief);
    }),"button primary");detail.append(prepare);
  }
  s.inquiries.forEach(i=>list.append(el("button",{class:"inquiry-button","data-id":i.id,onclick:()=>show(i)},el("span",{class:"eyebrow"},i.job_id?"CONVERTED TO JOB":"READY FOR REVIEW"),el("strong",{},i.subject.replace("Quote request — ","")),el("small",{},s.customers.find(c=>c.id===i.customer_id).name))));
  root.append(el("div",{class:"inbox-layout"},list,detail));
  if(s.inquiries.length)show(s.inquiries.find(i=>!i.job_id)||s.inquiries[0]);else detail.append(empty("No inquiries","Reset the demo to restore the example inquiries."));
}
function jobs(root,s,a){
  root.append(heading("JOB WORKSPACE","Every job, one clear picture.","Follow the work from reviewed inquiry to completion.",link("＋  Review new inquiries","#inbox","button primary")));
  const search=field("Search projects","search","","search",{placeholder:"Search by job, customer or location…"}),
    filter=selectField("Job status","status",[{id:"all",name:"All statuses"},...["draft","quoted","scheduled","in_progress","completed"].map(id=>({id,name:labelStatus(id)}))]),
    holder=el("div",{});
  search.classList.add("search-field");root.append(el("div",{class:"toolbar"},search,filter),holder);
  function draw(){
    const query=search.querySelector("input").value.toLowerCase(),st=filter.querySelector("select").value;
    const jobs=s.jobs.filter(j=>(st==="all"||j.status===st)&&[j.title,j.customer_name,j.site,j.number].join(" ").toLowerCase().includes(query));
    if(!jobs.length){holder.replaceChildren(empty("No matching jobs","Try another search or status filter."));return;}
    holder.replaceChildren(el("div",{class:"table-wrap"},el("table",{},el("thead",{},el("tr",{},["Project","Customer","Status","Quote value","Requested dates",""].map(t=>el("th",{},t)))),
      el("tbody",{},jobs.map(j=>el("tr",{},el("td",{},link(j.title,"#jobs/"+j.id),el("small",{},j.number+" · "+j.site)),el("td",{},j.customer_name),el("td",{},status(j.status)),el("td",{},j.quote_total===null?"—":money(j.quote_total)),el("td",{},day(j.requested_start)+"–"+day(j.requested_end)),el("td",{},link("Open ↗","#jobs/"+j.id))))))));
  }
  search.addEventListener("input",draw);filter.addEventListener("change",draw);draw();
}
let weekOffset=0;
function schedule(root,s,a){
  root.append(heading("PEOPLE & EQUIPMENT","Make room for the right work.","All-day reservations for your crews and equipment. Dates follow Toronto time."));
  const controls=el("div",{class:"actions"}),range=el("h2",{}),holder=el("div",{});
  controls.append(button("← Previous",()=>{weekOffset-=7;draw();}),button("This week",()=>{weekOffset=0;draw();}),button("Next →",()=>{weekOffset+=7;draw();}));
  root.append(el("div",{class:"toolbar"},range,controls),holder);
  function draw(){
    const dow=new Date(s.business_date+"T12:00:00Z").getUTCDay(),start=addDays(s.business_date,-((dow+6)%7)+weekOffset),end=addDays(start,6);
    range.textContent=day(start)+" – "+day(end);
    const grid=el("div",{class:"week-grid"}),list=el("div",{class:"schedule-list panel"}),visible=s.assignments.filter(x=>x.start_date<=end&&x.end_date>=start);
    for(let index=0;index<7;index++){
      const d=addDays(start,index),column=el("div",{class:"week-day"+(d===s.business_date?" today":"")},el("div",{class:"day-heading"},["MON","TUE","WED","THU","FRI","SAT","SUN"][index],el("strong",{},Number(d.slice(-2)))));
      visible.filter(x=>x.start_date<=d&&x.end_date>=d).forEach(x=>{
        const j=s.jobs.find(j=>j.id===x.job_id),crew=s.crews.find(c=>c.id===x.crew_id),equipment=s.equipment.find(e=>e.id===x.equipment_id);
        column.append(el("a",{href:"#jobs/"+j.id,class:"schedule-card"},el("strong",{},j.title),el("small",{},crew.name+" · "+equipment.name)));
      });grid.append(column);
    }
    visible.sort((x,y)=>x.start_date.localeCompare(y.start_date)).forEach(x=>{
      const j=s.jobs.find(j=>j.id===x.job_id);
      list.append(el("a",{class:"job-row",href:"#jobs/"+j.id},el("div",{class:"job-row-main"},el("h3",{},j.title),el("p",{},day(x.start_date)+" – "+day(x.end_date)+" · "+s.crews.find(c=>c.id===x.crew_id).name)),status(j.status)));
    });
    if(!visible.length)list.append(empty("No assignments this week","Try another week or schedule an approved job."));
    holder.replaceChildren(grid,list,el("p",{class:"legend"},"●  Crew and equipment reservations",el("span",{},"Inclusive dates · Open a job to reschedule")));
  }draw();
}
function integrations(root,s,a){
  root.append(heading("CONNECTED WORKFLOWS","See where the data goes.","Preview the handoff between your operations and business tools."));
  root.append(el("div",{class:"notice green"},"Demo mode · These connectors are not connected. Previews are stored locally and do not contact QuickBooks, email, calendar or CRM services."));
  const jobField=selectField("Project to preview","job_id",s.jobs.map(j=>({id:j.id,name:j.number+" · "+j.title}))),
    output=el("div",{class:"preview-output","aria-live":"polite"}),cards=el("div",{class:"connector-grid"});
  root.append(el("div",{class:"toolbar"},jobField),cards,output);
  s.integration.connectors.forEach(c=>{
    const error=formError(),preview=button("Preview local payload ↗",()=>run(preview,error,async()=>{
      const job=await a.job(jobField.querySelector("select").value);
      const result=await api("/api/jobs/"+job.id+"/integration-previews",{method:"POST",body:JSON.stringify({expected_version:job.version,connector:c.id})});
      output.replaceChildren(el("div",{class:"panel"},sectionHead(c.name+" · Local preview","Saved in your workspace. Nothing was sent."),el("pre",{},JSON.stringify(result.preview,null,2))));
      a.toast("Local preview saved. No data was sent.");await a.sync(); 
    }),"button");
    cards.append(el("section",{class:"panel connector connector-"+c.id},el("div",{class:"connector-icon"},({quickbooks:"qb",email_calendar:"↗",crm:"◎"}[c.id])),el("h2",{},c.name),el("span",{class:"status"},"Demo / Not connected"),el("p",{},c.description),
      el("div",{class:"mapping"},Object.entries(c.mapping).map(([key,value])=>el("div",{},el("strong",{},key),value))),error,preview));
  });
  if(s.integration.history.length)root.append(el("section",{class:"panel preview-output"},sectionHead("Recent local previews","Stored examples, never external sync receipts"),
    s.integration.history.slice().reverse().slice(0,5).map(p=>el("div",{class:"revision"},p.connector.replace("_"," ")+" · "+p.payload.title,button("View payload",()=>output.replaceChildren(el("pre",{},JSON.stringify(p,null,2))),"button small")))));
}
export function renderView(root,state,actions){
  ({overview,inbox,jobs,schedule,integrations}[state.page]||overview)(root,state,actions);
}
