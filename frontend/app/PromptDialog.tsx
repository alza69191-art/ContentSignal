"use client";
import { useEffect, useState } from "react";
import { X, Sparkles, WandSparkles, Check } from "lucide-react";

type Props = {
  open: boolean;
  initialPrompt: string;
  onClose: () => void;
  onApply: (prompt: string) => void;
};

const ideas = [
  "أضف حركة كاميرا سينمائية ناعمة",
  "اجعل الإضاءة واقعية وتفاصيل المشهد دقيقة",
  "حافظ على ثبات شكل الشخصية طوال اللقطة",
];

export default function PromptDialog({ open, initialPrompt, onClose, onApply }: Props) {
  const [draft, setDraft] = useState(initialPrompt);
  useEffect(() => { if (open) setDraft(initialPrompt); }, [open, initialPrompt]);
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  const addIdea = (idea: string) => setDraft(current => current.trim() ? current.trim() + "، " + idea : idea);
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="prompt-dialog" role="dialog" aria-modal="true" aria-labelledby="prompt-dialog-title" dir="rtl">
        <header className="dialog-header">
          <div className="dialog-heading"><span className="dialog-spark"><WandSparkles size={19}/></span><div><h2 id="prompt-dialog-title">مساعد صياغة المشهد</h2><p>رتّب وصفك وأضف تفاصيل تساعد نموذج الفيديو.</p></div></div>
          <button className="dialog-close" onClick={onClose} aria-label="إغلاق"><X size={19}/></button>
        </header>
        <div className="dialog-content">
          <label htmlFor="prompt-draft">وصف المشهد</label>
          <textarea id="prompt-draft" value={draft} onChange={event => setDraft(event.target.value)} rows={6} placeholder="اكتب ما الذي يظهر في المشهد، وما الحركة التي تحدث..."/>
          <span className="dialog-hint">إضافات مقترحة — اختر ما يناسب مشهدك</span>
          <div className="idea-list">{ideas.map(idea => <button type="button" key={idea} onClick={() => addIdea(idea)}><Sparkles size={14}/>{idea}</button>)}</div>
        </div>
        <footer className="dialog-footer"><button className="dialog-cancel" onClick={onClose}>إلغاء</button><button className="dialog-apply" onClick={() => { onApply(draft.trim()); onClose(); }} disabled={!draft.trim()}><Check size={17}/> اعتماد الوصف</button></footer>
      </section>
    </div>
  );
}
