"use client";
import { useState } from "react";
import { Film, Image as ImageIcon, Video, WandSparkles, Upload, Languages, Sparkles, Clock3, Clapperboard, MessageSquareText } from "lucide-react";
import PromptDialog from "./PromptDialog";

type Mode = "text" | "image" | "video";
const modes: {id:Mode;label:string;sub:string;icon:typeof Film}[] = [
  {id:"text",label:"نص إلى فيديو",sub:"ولّد فيديو من وصفك باستخدام Wan 2.2",icon:WandSparkles},
  {id:"image",label:"صورة إلى فيديو",sub:"حرّك صورك باستخدام Wan 2.2",icon:ImageIcon},
  {id:"video",label:"فيديو إلى فيديو",sub:"قريبًا — يحتاج سير عمل منفصل",icon:Video}
];
export default function Home() {
  const [mode,setMode] = useState<Mode>("text");
  const [prompt,setPrompt] = useState("");
  const [dialogOpen,setDialogOpen] = useState(false);
  const [file,setFile] = useState<File|null>(null);
  const [aspectRatio,setAspectRatio] = useState("16:9");
  const [duration,setDuration] = useState(2);
  const [quality,setQuality] = useState("standard");
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState("");
  const [outputUrl,setOutputUrl] = useState("");
  const [lang,setLang] = useState<"ar"|"en">("ar");
  const copy = lang==="ar";
  async function submit() {
    if(mode==="video"){setMessage("تحويل فيديو إلى فيديو غير مفعّل في إصدار Wan 2.2 الأول.");return;}
    if (!prompt.trim()) { setMessage("اكتب وصف الفيديو أولاً."); return; }
    if (mode==="image" && !file) { setMessage("اختر صورة أولاً."); return; }
    setBusy(true); setMessage(""); setOutputUrl("");
    const api = process.env.NEXT_PUBLIC_API_URL || "";
    try {
      const body = new FormData(); body.append("mode",mode); body.append("prompt",prompt);
      const [width,height] = aspectRatio==="9:16" ? [480,832] : aspectRatio==="1:1" ? [640,640] : [832,480];
      const frames = duration===2 ? 49 : duration===3 ? 73 : duration===4 ? 97 : 121;
      const steps = quality==="high" ? 24 : 20;
      body.append("width",String(width)); body.append("height",String(height));
      body.append("frames",String(frames)); body.append("steps",String(steps));
      if(file) body.append("file",file);
      const res = await fetch(api+"/api/jobs",{method:"POST",body});
      const data = await res.json();
      if(!res.ok) throw new Error(data.detail || "تعذر إرسال الطلب");
      setMessage("تم إرسال المهمة إلى Wan 2.2. رقم المهمة: "+data.job_id+" — جارٍ التوليد...");
      for(let attempt=0;attempt<180;attempt++){
        await new Promise(resolve=>setTimeout(resolve,3000));
        const statusResponse=await fetch(api+"/api/jobs/"+data.job_id);
        const statusData=await statusResponse.json();
        if(!statusResponse.ok) throw new Error(statusData.detail || "تعذر متابعة المهمة");
        if(statusData.status==="completed"){
          const output=statusData.output_files?.find((item:{url:string})=>item.url);
          if(output) setOutputUrl(output.url);
          setMessage("اكتمل التوليد بنجاح باستخدام Wan 2.2.");
          return;
        }
        if(statusData.status==="failed") throw new Error(statusData.message || "فشل توليد الفيديو");
      }
      setMessage("ما زالت المهمة قيد التنفيذ. احتفظ برقم المهمة لمتابعتها: "+data.job_id);
    } catch(e) { setMessage(e instanceof Error ? e.message : "حدث خطأ في الاتصال بالخادم."); }
    finally { setBusy(false); }
  }
  return <main className="shell">
    <header className="topbar"><a className="brand" href="#"><span className="brandmark"><Film size={22}/></span><span>Content<span className="accent">Signal</span></span></a><nav><a className="active" href="#">استوديو الفيديو</a><a href="#how">كيف يعمل</a></nav><button className="lang" onClick={()=>setLang(copy?"en":"ar")}><Languages size={17}/>{copy?"English":"العربية"}</button></header>
    <section className="hero"><div className="eyebrow"><Sparkles size={15}/> WAN 2.2 · OPEN SOURCE VIDEO</div><h1>{copy?"حوّل خيالك إلى فيديو":"Turn your ideas into video"}</h1><p>{copy?"أنشئ مقاطع فيديو من النصوص والصور باستخدام نموذج Wan 2.2 مفتوح المصدر.":"Create videos from text and images with the open-source Wan 2.2 model."}</p></section>
    <section className="workspace">
      <div className="section-head"><div><span className="step">01</span><div><h2>اختر طريقة الإنشاء</h2><p>ابدأ بالمصدر الذي تريد تحويله</p></div></div><span className="draft">Wan 2.2 · TI2V-5B</span></div>
      <div className="mode-grid">{modes.map(m=>{const Icon=m.icon;return <button key={m.id} disabled={m.id==="video"} className={"mode-card "+(mode===m.id?"selected":"")} onClick={()=>{setMode(m.id);setFile(null);setMessage("");setOutputUrl("");}}><span className="mode-icon"><Icon size={21}/></span><span className="mode-title">{m.label}</span><span className="mode-sub">{m.sub}</span></button>})}</div>
      <div className="section-head second"><div><span className="step">02</span><div><h2>{mode==="text"?"اكتب وصف الفيديو":"أضف الصورة"}</h2><p>{mode==="text"?"صف المشهد الذي تريد رؤيته بالتفصيل":"اختر صورة ثم أضف تعليمات الحركة المطلوبة"}</p></div></div></div>
      {mode==="image"&&<label className="upload"><Upload size={24}/><strong>{file?file.name:"اسحب الصورة إلى هنا أو اضغط للاختيار"}</strong><span>PNG, JPG, WEBP</span><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>setFile(e.target.files?.[0]||null)}/></label>}
      <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder={mode==="text"?"مثال: لقطة سينمائية لتنين وردي يحلّق فوق قلعة قديمة عند الغروب، إضاءة واقعية وتفاصيل دقيقة...":"اكتب كيف تريد تحريك الصورة..."} rows={5}/>
      <div className="prompt-tools"><span>اكتب وصفًا واضحًا للمشهد والحركة والإضاءة.</span><button type="button" onClick={()=>setDialogOpen(true)}><MessageSquareText size={16}/> فتح مساعد صياغة</button></div>
      <div className="controls"><div className="control"><label>نسبة الأبعاد</label><select value={aspectRatio} onChange={e=>setAspectRatio(e.target.value)}><option value="16:9">16:9 — شاشة عريضة</option><option value="9:16">9:16 — عمودي</option><option value="1:1">1:1 — مربع</option></select></div><div className="control"><label>المدة المستهدفة</label><select value={duration} onChange={e=>setDuration(Number(e.target.value))}><option value={2}>2 ثانية</option><option value={3}>3 ثوانٍ</option><option value={4}>4 ثوانٍ</option><option value={5}>5 ثوانٍ</option></select></div><div className="control"><label>الجودة</label><select value={quality} onChange={e=>setQuality(e.target.value)}><option value="standard">قياسية — 20 خطوة</option><option value="high">عالية — 24 خطوة</option></select></div></div>
      <button className="generate" onClick={submit} disabled={busy}>{busy?"جارٍ التوليد...":<><Sparkles size={18}/> توليد الفيديو باستخدام Wan 2.2</>}</button>
      {message&&<div className="notice">{message}</div>}
      {outputUrl&&<video className="result-video" controls src={outputUrl}/>}
      <p className="disclaimer">يتطلب تشغيل ComfyUI وتحميل نموذج Wan 2.2 وإعداد ملف Workflow بصيغة API على الخادم.</p>
    </section>
    <section className="bottom" id="how"><div><Clapperboard size={19}/><span>مساحة إنتاجك الإبداعية</span></div><span><Clock3 size={15}/> توليد مفتوح المصدر عبر Wan 2.2</span></section>
    <footer>© 2026 ContentSignal · AI Video Studio</footer>
    <PromptDialog open={dialogOpen} initialPrompt={prompt} onClose={()=>setDialogOpen(false)} onApply={setPrompt}/>
  </main>;
}
