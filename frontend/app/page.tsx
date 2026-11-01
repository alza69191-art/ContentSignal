"use client";
import { useState } from "react";
import { Film, Image as ImageIcon, Video, WandSparkles, Upload, Languages, Sparkles, Clock3, Clapperboard } from "lucide-react";

type Mode = "text" | "image" | "video";
const modes: {id:Mode;label:string;sub:string;icon:typeof Film}[] = [
  {id:"text",label:"نص إلى فيديو",sub:"حوّل وصفك إلى مشهد سينمائي",icon:WandSparkles},
  {id:"image",label:"صورة إلى فيديو",sub:"حرّك صورك واجعلها تنبض بالحياة",icon:ImageIcon},
  {id:"video",label:"فيديو إلى فيديو",sub:"حوّل أسلوب ومظهر الفيديو",icon:Video}
];
export default function Home() {
  const [mode,setMode] = useState<Mode>("text");
  const [prompt,setPrompt] = useState("");
  const [file,setFile] = useState<File|null>(null);
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState("");
  const [lang,setLang] = useState<"ar"|"en">("ar");
  async function submit() {
    if (!prompt.trim() && mode==="text") { setMessage("اكتب وصف الفيديو أولاً."); return; }
    if (mode!=="text" && !file) { setMessage("اختر ملفًا أولاً."); return; }
    setBusy(true); setMessage("");
    try {
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const body = new FormData(); body.append("mode",mode); body.append("prompt",prompt);
      if(file) body.append("file",file);
      const res = await fetch(api+"/api/jobs",{method:"POST",body});
      const data = await res.json();
      if(!res.ok) throw new Error(data.detail || "تعذر إرسال الطلب");
      setMessage("تم استلام طلبك. رقم المهمة: "+data.job_id+" — محرك التوليد غير مربوط بعد.");
    } catch(e) { setMessage(e instanceof Error ? e.message : "حدث خطأ في الاتصال بالخادم."); }
    finally { setBusy(false); }
  }
  const copy = lang==="ar";
  return <main className="shell">
    <header className="topbar"><a className="brand" href="#"><span className="brandmark"><Film size={22}/></span><span>Content<span className="accent">Signal</span></span></a><nav><a className="active" href="#">استوديو الفيديو</a><a href="#how">كيف يعمل</a></nav><button className="lang" onClick={()=>setLang(copy?"en":"ar")}><Languages size={17}/>{copy?"English":"العربية"}</button></header>
    <section className="hero"><div className="eyebrow"><Sparkles size={15}/> AI VIDEO STUDIO</div><h1>{copy?"حوّل خيالك إلى فيديو":"Turn your ideas into video"}</h1><p>{copy?"أنشئ مقاطع فيديو من النصوص والصور والفيديوهات، من مساحة عمل واحدة.":"Create videos from text, images and footage in one workspace."}</p></section>
    <section className="workspace">
      <div className="section-head"><div><span className="step">01</span><div><h2>اختر طريقة الإنشاء</h2><p>ابدأ بالمصدر الذي تريد تحويله</p></div></div><span className="draft">نسخة تجريبية أولية</span></div>
      <div className="mode-grid">{modes.map(m=>{const Icon=m.icon;return <button key={m.id} className={"mode-card "+(mode===m.id?"selected":"")} onClick={()=>{setMode(m.id);setFile(null);setMessage("");}}><span className="mode-icon"><Icon size={21}/></span><span className="mode-title">{m.label}</span><span className="mode-sub">{m.sub}</span></button>})}</div>
      <div className="section-head second"><div><span className="step">02</span><div><h2>{mode==="text"?"اكتب وصف الفيديو":mode==="image"?"أضف الصورة":"أضف الفيديو"}</h2><p>{mode==="text"?"صف المشهد الذي تريد رؤيته بالتفصيل":"اختر ملفًا من جهازك ثم أضف تعليمات التحويل"}</p></div></div></div>
      {mode!=="text"&&<label className="upload"><Upload size={24}/><strong>{file?file.name:"اسحب الملف إلى هنا أو اضغط للاختيار"}</strong><span>{mode==="image"?"PNG, JPG, WEBP":"MP4, MOV, WEBM"}</span><input type="file" accept={mode==="image"?"image/*":"video/*"} onChange={e=>setFile(e.target.files?.[0]||null)}/></label>}
      <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder={mode==="text"?"مثال: لقطة سينمائية لتنين وردي يحلّق فوق قلعة قديمة عند الغروب، إضاءة واقعية وتفاصيل دقيقة...":"اكتب كيف تريد أن يبدو الفيديو الناتج..."} rows={5}/>
      <div className="controls"><div className="control"><label>نسبة الأبعاد</label><select><option>16:9 — شاشة عريضة</option><option>9:16 — عمودي</option><option>1:1 — مربع</option></select></div><div className="control"><label>المدة المستهدفة</label><select><option>5 ثوانٍ</option><option>10 ثوانٍ</option><option>15 ثانية</option></select></div><div className="control"><label>الجودة</label><select><option>قياسية</option><option>عالية</option></select></div></div>
      <button className="generate" onClick={submit} disabled={busy}>{busy?"جارٍ إرسال الطلب...":<><Sparkles size={18}/> تجهيز طلب الفيديو</>}</button>
      {message&&<div className="notice">{message}</div>}
      <p className="disclaimer">ملاحظة: هذه نسخة تأسيسية. إرسال الطلب يعمل بعد تشغيل الخادم، وسيتم تفعيل التوليد الفعلي بعد ربط مزود أو نموذج فيديو.</p>
    </section>
    <section className="bottom" id="how"><div><Clapperboard size={19}/><span>مساحة إنتاجك الإبداعية</span></div><span><Clock3 size={15}/> قريبًا: سجل المشاريع وتتبع التوليد</span></section>
    <footer>© 2026 ContentSignal · AI Video Studio</footer>
  </main>;
}
