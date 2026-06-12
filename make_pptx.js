// Usage: node make_pptx.js '<json_string>' '/output/path.pptx'
const pptxgen = require("pptxgenjs");
const data = JSON.parse(process.argv[2]);
const outPath = process.argv[3];

const BG   = "FFF9F0";
const DARK = "3D2B1F";
const MID  = "7D5A4A";
const ACC  = "FF7043";
const PALE = "FFF0E6";
const GRN  = "E8F5E9";
const GRN2 = "2E7D32";
const YLW  = "FFF8E1";
const YLW2 = "E65100";
const BLU  = "E3F2FD";
const BLU2 = "1565C0";
const PNK  = "FCE4EC";
const PNK2 = "880E4F";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = data.title || "그림책 질문수업";

// ── 슬라이드 1: 타이틀 ──────────────────────────────────────────
{
  const s = pres.addSlide();
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:5.625, fill:{color:BG} });
  // 책 아이콘 원
  s.addShape(pres.shapes.OVAL, { x:4.25, y:0.4, w:1.5, h:1.5, fill:{color:PALE}, line:{color:ACC,width:2} });
  s.addText("📚", { x:4.25, y:0.45, w:1.5, h:1.4, fontSize:32, align:"center", valign:"middle" });
  // 제목
  s.addText(data.title, {
    x:0.6, y:2.1, w:8.8, h:1.1,
    fontSize:28, bold:true, color:DARK, align:"center", fontFace:"나눔고딕"
  });
  s.addText(data.subtitle || "", {
    x:1, y:3.3, w:8, h:0.5,
    fontSize:14, color:MID, align:"center", fontFace:"나눔고딕"
  });
  // 꾸밈 점선
  s.addShape(pres.shapes.LINE, { x:2.5, y:4.0, w:5, h:0, line:{color:ACC,width:1,dashType:"sysDash"} });
  s.addText(data.grade + " · " + data.theme, {
    x:1, y:4.2, w:8, h:0.4,
    fontSize:12, color:MID, align:"center", fontFace:"나눔고딕"
  });
}

// ── 슬라이드 2: 수업 개요 ────────────────────────────────────────
{
  const s = pres.addSlide();
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:5.625, fill:{color:BG} });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x:0.3, y:0.2, w:2.5, h:0.55,
    fill:{color:ACC}, rectRadius:0.1, line:{color:ACC,width:0}
  });
  s.addText("수업 개요", { x:0.3, y:0.2, w:2.5, h:0.55, fontSize:13, bold:true, color:"FFFFFF", align:"center", fontFace:"나눔고딕" });

  const infoItems = [
    ["📗 그림책", data.book],
    ["🎯 주제", data.theme],
    ["⏰ 시간", data.lesson_time],
    ["📌 학년", data.grade],
  ];
  infoItems.forEach(([label, val], i) => {
    const x = (i % 2) * 4.8 + 0.4;
    const y = 1.0 + Math.floor(i / 2) * 1.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w:4.4, h:0.85, fill:{color:"FFFFFF"}, rectRadius:0.1,
      shadow:{type:"outer",color:"000000",blur:4,offset:2,angle:45,opacity:0.06} });
    s.addText(label, { x:x+0.15, y:y+0.05, w:1.3, h:0.35, fontSize:10, color:ACC, bold:true, fontFace:"나눔고딕" });
    s.addText(val, { x:x+0.15, y:y+0.38, w:4.1, h:0.38, fontSize:13, color:DARK, fontFace:"나눔고딕" });
  });

  // 목표
  s.addText("✅ 수업 목표", { x:0.4, y:3.2, w:9, h:0.35, fontSize:11, bold:true, color:ACC, fontFace:"나눔고딕" });
  if (data.objectives && data.objectives.length) {
    const objs = data.objectives.slice(0,3);
    objs.forEach((obj, i) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x:0.4, y:3.65+i*0.45, w:9.2, h:0.38,
        fill:{color:PALE}, rectRadius:0.08, line:{color:ACC,width:0.5}
      });
      s.addText(`${i+1}. ${obj}`, {
        x:0.6, y:3.65+i*0.45, w:9, h:0.38,
        fontSize:11, color:DARK, valign:"middle", fontFace:"나눔고딕"
      });
    });
  }
}

// ── 슬라이드 3~5: 질문 카드 (유형별) ────────────────────────────
const qTypes = [
  { key:"before",  label:"읽기 전 질문",  color:GRN,  tc:GRN2, icon:"🌱" },
  { key:"during",  label:"읽는 중 질문",  color:YLW,  tc:YLW2, icon:"🔍" },
  { key:"after",   label:"읽은 후 질문",  color:BLU,  tc:BLU2, icon:"💬" },
];

qTypes.forEach(({key, label, color, tc, icon}) => {
  const qs = (data.questions && data.questions[key]) || [];
  if (!qs.length) return;
  const s = pres.addSlide();
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:5.625, fill:{color:BG} });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x:0.3, y:0.2, w:3, h:0.55, fill:{color:tc}, rectRadius:0.1, line:{color:tc,width:0}
  });
  s.addText(icon + " " + label, {
    x:0.3, y:0.2, w:3, h:0.55, fontSize:13, bold:true, color:"FFFFFF", align:"center", fontFace:"나눔고딕"
  });

  const cols = qs.length > 3 ? 2 : 1;
  const perCol = Math.ceil(qs.length / cols);
  qs.slice(0, 6).forEach((q, i) => {
    const col = cols === 2 ? Math.floor(i / perCol) : 0;
    const row = cols === 2 ? i % perCol : i;
    const cardW = cols === 2 ? 4.5 : 9.2;
    const x = cols === 2 ? 0.3 + col * 5 : 0.4;
    const y = 1.0 + row * 1.3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w:cardW, h:1.1,
      fill:{color:color}, rectRadius:0.12,
      shadow:{type:"outer",color:"000000",blur:4,offset:2,angle:45,opacity:0.07}
    });
    // 질문 유형 태그
    const tag = q.type || "";
    if (tag) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x:x+0.1, y:y+0.08, w:0.9, h:0.25,
        fill:{color:tc}, rectRadius:0.06, line:{color:tc,width:0}
      });
      s.addText(tag, { x:x+0.1, y:y+0.08, w:0.9, h:0.25, fontSize:8, bold:true, color:"FFFFFF", align:"center", fontFace:"나눔고딕" });
    }
    s.addText(q.text || q, {
      x:x+0.12, y:y+0.38, w:cardW-0.24, h:0.65,
      fontSize:11, color:DARK, fontFace:"나눔고딕", wrap:true
    });
  });
});

// ── 슬라이드 6: 활동 흐름 ────────────────────────────────────────
{
  const s = pres.addSlide();
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:5.625, fill:{color:BG} });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x:0.3, y:0.2, w:2.5, h:0.55, fill:{color:ACC}, rectRadius:0.1, line:{color:ACC,width:0}
  });
  s.addText("🎨 수업 활동", { x:0.3, y:0.2, w:2.5, h:0.55, fontSize:13, bold:true, color:"FFFFFF", align:"center", fontFace:"나눔고딕" });

  const acts = data.activities || [
    {icon:"🔔", title:"도입 활동", desc:"배경지식 활성화 및 그림책 표지 탐색"},
    {icon:"📖", title:"중심 활동", desc:"대화형 읽기 및 질문-토론"},
    {icon:"✍️", title:"정리 활동", desc:"표현 활동 및 성찰"},
  ];
  const actColors = [GRN, YLW, PNK];
  const actTC = [GRN2, YLW2, PNK2];
  acts.slice(0,3).forEach((act, i) => {
    const x = 0.4 + i * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y:1.0, w:2.9, h:3.8,
      fill:{color:actColors[i]}, rectRadius:0.15,
      shadow:{type:"outer",color:"000000",blur:5,offset:2,angle:45,opacity:0.08}
    });
    s.addShape(pres.shapes.OVAL, { x:x+1.05, y:1.1, w:0.8, h:0.8, fill:{color:actTC[i]}, line:{color:actTC[i],width:0} });
    s.addText(act.icon || `${i+1}`, { x:x+1.05, y:1.1, w:0.8, h:0.8, fontSize:16, align:"center", valign:"middle", color:"FFFFFF" });
    s.addText(`활동 ${i+1}`, { x, y:2.1, w:2.9, h:0.3, fontSize:9, color:actTC[i], bold:true, align:"center", fontFace:"나눔고딕" });
    s.addText(act.title, { x, y:2.4, w:2.9, h:0.4, fontSize:13, bold:true, color:DARK, align:"center", fontFace:"나눔고딕" });
    s.addShape(pres.shapes.LINE, { x:x+0.3, y:2.85, w:2.3, h:0, line:{color:actTC[i],width:0.5,dashType:"sysDash"} });
    s.addText(act.desc, {
      x:x+0.15, y:2.95, w:2.6, h:1.7,
      fontSize:10, color:MID, wrap:true, valign:"top", fontFace:"나눔고딕"
    });
  });
  // 화살표
  s.addShape(pres.shapes.LINE, { x:3.35, y:2.85, w:0.4, h:0, line:{color:ACC,width:2} });
  s.addShape(pres.shapes.LINE, { x:6.45, y:2.85, w:0.4, h:0, line:{color:ACC,width:2} });
}

// ── 슬라이드 7: 평가 기준 ────────────────────────────────────────
{
  const s = pres.addSlide();
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:5.625, fill:{color:BG} });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x:0.3, y:0.2, w:2.5, h:0.55, fill:{color:ACC}, rectRadius:0.1, line:{color:ACC,width:0}
  });
  s.addText("⭐ 평가", { x:0.3, y:0.2, w:2.5, h:0.55, fontSize:13, bold:true, color:"FFFFFF", align:"center", fontFace:"나눔고딕" });

  const evals = data.evaluations || [
    {criterion:"그림책 내용 이해", good:"내용을 정확히 이해하고 설명한다", ok:"대략적인 내용을 이해한다", need:"교사의 도움이 필요하다"},
    {criterion:"질문 생성 능력", good:"다양한 유형의 질문을 스스로 만든다", ok:"교사 도움으로 질문을 만든다", need:"질문 만들기에 어려움을 느낀다"},
  ];
  const header = ["평가 기준", "충분", "보통", "노력 필요"];
  const hColors = [DARK, GRN2, YLW2, "C62828"];
  const hBGs = [PALE, GRN, YLW, PNK];
  const colX = [0.3, 2.8, 5.4, 7.7];
  const colW = [2.4, 2.5, 2.2, 2.2];

  header.forEach((h, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x:colX[i], y:0.95, w:colW[i], h:0.38,
      fill:{color:hBGs[i]}, rectRadius:0.06, line:{color:hColors[i],width:0.5}
    });
    s.addText(h, { x:colX[i], y:0.95, w:colW[i], h:0.38, fontSize:11, bold:true, color:hColors[i], align:"center", fontFace:"나눔고딕" });
  });

  evals.slice(0,3).forEach((ev, i) => {
    const y = 1.45 + i * 1.3;
    [ev.criterion, ev.good, ev.ok, ev.need].forEach((txt, j) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x:colX[j], y, w:colW[j], h:1.15,
        fill:{color: j===0 ? PALE : "FFFFFF"}, line:{color:"E8C9A0",width:0.5}
      });
      s.addText(txt, {
        x:colX[j]+0.1, y:y+0.05, w:colW[j]-0.2, h:1.05,
        fontSize:10, color:j===0?DARK:MID, wrap:true, valign:"middle", fontFace:"나눔고딕"
      });
    });
  });
}

// ── 슬라이드 8: 학부모 안내문 ───────────────────────────────────
{
  const s = pres.addSlide();
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:5.625, fill:{color:BG} });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x:0.3, y:0.2, w:3, h:0.55, fill:{color:ACC}, rectRadius:0.1, line:{color:ACC,width:0}
  });
  s.addText("👨‍👩‍👧 학부모 안내문", { x:0.3, y:0.2, w:3, h:0.55, fontSize:13, bold:true, color:"FFFFFF", align:"center", fontFace:"나눔고딕" });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x:0.4, y:0.95, w:9.2, h:3.8,
    fill:{color:"FFFFFF"}, rectRadius:0.15,
    shadow:{type:"outer",color:"000000",blur:6,offset:2,angle:45,opacity:0.07}
  });
  const msgLines = data.parent_message || [
    `오늘 우리 반은 「${data.book}」을(를) 함께 읽었습니다.`,
    `주제: ${data.theme}`,
    "",
    "💬 가정에서 나눌 수 있는 대화 질문",
    "① 오늘 읽은 그림책에서 가장 기억에 남는 장면이 있나요?",
    "② 책 속 인물의 마음이 어떠했을 것 같나요?",
    "③ 우리 가족에게도 비슷한 경험이 있었나요?",
  ];
  s.addText(msgLines.map((l,i)=>({
    text: l + (i<msgLines.length-1?"\n":""),
    options: { fontSize:11, color: l.startsWith("💬")? ACC : DARK, bold: l.startsWith("💬"), fontFace:"나눔고딕" }
  })), { x:0.7, y:1.1, w:8.6, h:3.5 });
}

// ── 슬라이드 9: 마무리 ──────────────────────────────────────────
{
  const s = pres.addSlide();
  s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:5.625, fill:{color:PALE} });
  s.addText("📚", { x:4.3, y:1.0, w:1.4, h:1.4, fontSize:48, align:"center" });
  s.addText(data.title, {
    x:0.5, y:2.6, w:9, h:0.8,
    fontSize:22, bold:true, color:DARK, align:"center", fontFace:"나눔고딕"
  });
  s.addShape(pres.shapes.LINE, { x:3, y:3.5, w:4, h:0, line:{color:ACC,width:1,dashType:"sysDash"} });
  s.addText("수업을 마치며 — " + data.grade, {
    x:1, y:3.65, w:8, h:0.4,
    fontSize:13, color:MID, align:"center", fontFace:"나눔고딕"
  });
  s.addText("만든이: 울산초 교사 신재광", {
    x:1, y:4.8, w:8, h:0.3,
    fontSize:10, color:MID, align:"right", fontFace:"나눔고딕"
  });
}

pres.writeFile({ fileName: outPath }).then(() => {
  console.log("OK:" + outPath);
}).catch(e => {
  console.error("ERR:" + e.message);
  process.exit(1);
});
