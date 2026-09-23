import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
const runtime='C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=JSON.parse(await fs.readFile(path.join(root,'outputs/deck_data.json'),'utf8'));
const build=path.join(root,'.build'); await fs.mkdir(build,{recursive:true});
const family=resolvePresentationFont();
const p=Presentation.create({slideSize:{width:1280,height:720}});
const source='Source: London Fire Brigade Mobilisation Records; snapshot SHA256 in data/source_manifest.json. Computations: scripts/analysis.py; outputs/*_metrics.csv. https://data.london.gov.uk/dataset/london-fire-brigade-mobilisation-records-24r65';
function text(s,value,x,y,w,h,size=29,color='#24292e',bold=false){
 const box=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 box.text=value;box.text.style={typeface:family,fontSize:size,color,bold,autoFit:'none'};return box;
}
function slide(title,note=''){
 const s=p.slides.add();s.background.fill='#ffffff';
 text(s,title,64,42,1152,94,43,'#24292e',true);
 s.speakerNotes.textFrame.setText(source+'\n'+note);
 return s;
}
function body(s,paragraphs){paragraphs.forEach((v,i)=>text(s,v,72,170+i*115,1120,100,29));}
function chart(s,type,categories,series,opts={}){
 series=series.map(item=>({...item,values:item.values.map(v=>Number(v.toFixed(6))),valuesFormatCode:'0.00'}));
 const c=s.charts.add(type,{position:{left:90,top:175,width:1100,height:415},categories,series,hasLegend:series.length>1,
  legend:{position:'top',textStyle:{fontSize:19}},lineOptions:{smooth:false},
  xAxis:{textStyle:{fontSize:16},majorGridlines:null},yAxis:{min:0,title:'Minutes',numberFormatCode:'0.0',textStyle:{fontSize:18},majorGridlines:{fill:'#dddddd',width:1}},...opts});
 applyPresentationChartFont(c,{fontFamily:family});return c;
}
function foot(s,value){text(s,value,72,616,1120,70,22,'#555555');}
let s=slide('London Fire Brigade','Team review remains required. AI assistance is disclosed in PROCESS_LOG.md.');
text(s,'Mobilisation-to-arrival analysis',72,195,1120,90,48,'#287c8e',true);
text(s,'C1 | Business Intelligence\nMatias Muñoz Hoffmann and Clemente Ibarra\n29 September 2026',72,350,1100,190,30);
s=slide('Decision and scope');
body(s,['Prioritise boroughs and dispatch hours for operational review.','One row represents one vehicle mobilisation, not one emergency.','Published records in 2023-2024; 31 December 2024 is absent.','Results support investigation, not automatic resource allocation.']);
s=slide('KPI: P90 mobilisation-to-arrival time');
body(s,['P90 of AttendanceTimeSeconds / 60 among eligible records.','Approximately 90% of observed durations fall at or below P90.','Report monthly by borough, with median, eligible volume and exclusions.','The clock starts at mobilisation; call handling is outside this measure.']);
s=slide('Data quality and cleaning');
body(s,[`${data.audit.raw_rows.toLocaleString('en-US')} original rows; ${data.audit.exact_duplicates_removed.toLocaleString('en-US')} exact duplicates removed across 2021-2024.`,
`${data.audit.period_rows_after_exact_dedup.toLocaleString('en-US')} selected-period rows; ${data.audit.excluded_kpi_rows} conflicting-ID rows excluded.`,
`${data.audit.eligible_kpi_rows.toLocaleString('en-US')} eligible mobilisations across ${data.audit.distinct_incidents_in_eligible.toLocaleString('en-US')} incident IDs.`,
'No target imputation; no additional outlier trimming. Timestamp totals reconciled.']);
s=slide('Coverage and selection limits','LFB FOI 8420.1 dated 5 February 2024: https://www.london-fire.gov.uk/media/8863/foia84201-response-times-of-fire-brigades-and-data-collation-response.pdf . Its >20-minute counting exclusion is consistent with the extract ceiling, but exact CSV filters remain unverified.');
body(s,['All observed records are Initial mobilisations; durations stop at 20 minutes.','LFB documents >20-minute exclusions in published performance calculations.','The extract cannot describe the unobserved extreme tail.','Unknown borough: 1,288 eligible records. Missing day: 31 December 2024.']);
s=slide('Attendance-time distribution');
chart(s,'bar',data.histogram.categories,[{name:'Mobilisations',values:data.histogram.values,fill:'#287c8e'}],{barOptions:{direction:'column',gapWidth:5},yAxis:{min:0,title:'Mobilisations',numberFormatCode:'#,##0',textStyle:{fontSize:18}},xAxis:{title:'Minutes, 1-minute bins',textStyle:{fontSize:15}}});
foot(s,`Median ${data.summary.median_min.toFixed(2)} min | P90 ${data.summary.p90_min.toFixed(2)} min | Full observed range included.`);
s=slide('Smoothed attendance-time density');
chart(s,'line',data.density.categories.filter((v,i)=>i%2===0),[{name:'Density',values:data.density.values.filter((v,i)=>i%2===0),line:{fill:'#287c8e',width:3}}],{yAxis:{min:0,title:'Density',numberFormatCode:'0.00',textStyle:{fontSize:18}},xAxis:{title:'Minutes',textStyle:{fontSize:16}}});
foot(s,'Deterministic 20,000-record sample; KDE reflected at zero. Display only, not a prediction model.');
s=slide('Monthly median and P90');
chart(s,'line',data.monthly.map(r=>r.month),[
 {name:'P90',values:data.monthly.map(r=>r.p90_min),line:{fill:'#ad4932',width:3}},
 {name:'Median',values:data.monthly.map(r=>r.median_min),line:{fill:'#287c8e',width:3}}
],{xAxis:{textStyle:{fontSize:12}}});
foot(s,'December 2024 lacks its final day. Changes are descriptive; case mix is not controlled.');
s=slide('Highest observed borough P90 values');
const top=data.borough.filter(r=>r.borough!=='Unknown').sort((a,b)=>b.p90_min-a.p90_min).slice(0,5);
chart(s,'bar',top.map(r=>`${r.borough} (n=${r.n.toLocaleString('en-US')})`),[{name:'P90 minutes',values:top.map(r=>r.p90_min),fill:'#287c8e'}],{barOptions:{direction:'bar'},xAxis:{textStyle:{fontSize:18}},yAxis:{title:'Minutes',min:0,max:12,textStyle:{fontSize:20}},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:20}}});
foot(s,'Unadjusted published mobilisation times; differences do not establish crew performance or causes.');
s=slide('Dispatch-hour profile');
chart(s,'line',data.hour.map(r=>String(r.hour_gmt)),[{name:'P90',values:data.hour.map(r=>r.p90_min),line:{fill:'#ad4932',width:3}},{name:'Median',values:data.hour.map(r=>r.median_min),line:{fill:'#287c8e',width:3}}],{xAxis:{title:'Dispatch hour GMT',textStyle:{fontSize:17}}});
foot(s,'Highest pooled P90: 11:00 GMT, 10.03 min. This association does not isolate traffic effects.');
s=slide('Correlation and interpretation');
const corr=data.correlations.AttendanceTimeSeconds;
body(s,[`Spearman total versus travel: ${corr.TravelTimeSeconds.toFixed(3)}.`,
`Spearman total versus turnout: ${corr.TurnoutTimeSeconds.toFixed(3)}.`,
'Total attendance contains both components, so correlation is partly arithmetic.',
'Realised component times must not be used as dispatch-time predictors in C2.']);
s=slide('Operational review and C2');
body(s,['Proposed review rule: borough P90 above monthly global P90 for 3 consecutive months, with n >= 100 each month.',
'The rule is an academic heuristic; sensitivity results are in the notebook.',
'First investigate case mix, missing geography and source eligibility.',
'C2: compare a baseline and models with temporal validation; incorporate C1 feedback.']);
s=slide('Reproducibility and responsibility');
body(s,['Original CSV and dictionary: official source URLs and SHA256 manifest.',
'Notebook: executable pipeline, quality checks, tables and nine visual analyses.',
'AI assistance disclosed; both students must verify and explain every decision.',
'Submit the private GitHub URL and full commit SHA; verify instructor access.']);
await (await PresentationFile.exportPptx(p)).save(path.join(build,'candidate.pptx'));
const finalPath=path.join(root,'outputs/C1_LFB_reviewed.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(build,'candidate.pptx'),finalPath,
 pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 requiredNativeChartOwnerSlides:[6,7,8,9,10],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[family]},
 verifyArtifactToolImport:true,receiptPath:path.join(build,'presentation-reviewed.validation.json')});
console.log(JSON.stringify({path:result.finalPath,sha:result.finalSha256,charts:result.nativeChartValidation.passed}));
const rendered=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<rendered.slides.items.length;i++){
 const preview=await rendered.export({slide:rendered.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await preview.arrayBuffer()));
}
