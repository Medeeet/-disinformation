const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Қазақстан БАҚ-ындағы дезинформацияны анықтау жүйесі";

const C = {
  deep:      "0A2342",
  mid:       "1A3F6F",
  teal:      "0D7E8A",
  tealLt:    "14A5B3",
  white:     "FFFFFF",
  offWhite:  "F4F7F9",
  gray:      "64748B",
  lightGray: "E2E8F0",
  text:      "1E293B",
  green:     "059669",
  amber:     "D97706",
  red:       "DC2626",
};

const shadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12
});

const header = (s, title) => {
  s.background = { color: C.offWhite };
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.75,
    fill: { color: C.deep }, line: { color: C.deep }
  });
  s.addText(title, {
    x: 0.4, y: 0, w: 9, h: 0.75,
    fontSize: 20, fontFace: "Trebuchet MS", bold: true,
    color: C.white, align: "left", valign: "middle", margin: 0
  });
};

const card = (s, x, y, w, h, accentColor) => {
  s.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: C.white }, line: { color: C.lightGray, width: 1 }, shadow: shadow()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.12, h,
    fill: { color: accentColor }, line: { color: accentColor }
  });
};

const bullet = (s, x, y, text, color) => {
  s.addShape(pres.shapes.OVAL, {
    x, y: y + 0.08, w: 0.14, h: 0.14,
    fill: { color }, line: { color }
  });
  s.addText(text, {
    x: x + 0.22, y, w: 3.6, h: 0.36,
    fontSize: 12, fontFace: "Calibri", color: C.text,
    align: "left", valign: "middle", margin: 0
  });
};

// ─── SLIDE 1 — Титул ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.75,
    fill: { color: C.deep }, line: { color: C.deep }
  });
  s.addText("ДЕЗИНФОРМАЦИЯНЫ АНЫҚТАУ ЖҮЙЕСІ", {
    x: 0.4, y: 0, w: 9, h: 0.75,
    fontSize: 22, fontFace: "Trebuchet MS", bold: true,
    color: C.white, align: "left", valign: "middle", margin: 0
  });

  s.addText("ҚАЗАҚСТАН БАҚ-ЫНДАҒЫ\nДЕЗИНФОРМАЦИЯНЫ АНЫҚТАУ ЖҮЙЕСІ", {
    x: 0.4, y: 1.0, w: 7.0, h: 1.4,
    fontSize: 32, fontFace: "Trebuchet MS", bold: true,
    color: C.deep, align: "left", margin: 0
  });
  s.addText("Машиналық оқыту мен лингвистикалық ережелер негізінде", {
    x: 0.4, y: 2.55, w: 7.0, h: 0.6,
    fontSize: 16, fontFace: "Calibri", color: C.gray,
    align: "left", margin: 0
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 3.3, w: 4.2, h: 0.04,
    fill: { color: C.teal }, line: { color: C.teal }
  });
  s.addText("ruBert-base  ·  FastAPI  ·  ONNX  ·  Қазақ және орыс тілдері  ·  2025", {
    x: 0.4, y: 3.45, w: 9.0, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.teal, align: "left", margin: 0
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.5, y: 0.9, w: 2.15, h: 4.4,
    fill: { color: C.teal, transparency: 90 }, line: { color: C.teal, transparency: 70 }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 8.5, y: 0.9, w: 1.15, h: 4.4,
    fill: { color: C.teal, transparency: 80 }, line: { color: C.teal, transparency: 60 }
  });
}

// ─── SLIDE 2 — Мәселе ─────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "МӘСЕЛЕ ЖӘНЕ МАҚСАТ");

  card(s, 0.35, 1.0, 4.2, 4.25, C.red);
  s.addText("Мәселе", {
    x: 0.6, y: 1.12, w: 3.8, h: 0.42,
    fontSize: 15, fontFace: "Trebuchet MS", bold: true, color: C.text, margin: 0
  });
  s.addText(
    "Қазақстан медиакеңістігіндегі дезинформация ағыны жыл сайын өсуде.\n\n" +
    "Қоғам орыс және қазақ тілдерінде жұмыс жасайды — бұл автоматтандырылған талдауды айтарлықтай қиындатады.\n\n" +
    "Болыстық деңгейде дезинформацияны анықтайтын арнайы KZ-контекстік құралдар жоқ.\n\n" +
    "Жалған жаңалықтар саяси, экономикалық және қоғамдық зиян тигізеді.",
    {
      x: 0.6, y: 1.62, w: 3.8, h: 3.45,
      fontSize: 12, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    }
  );

  card(s, 5.45, 1.0, 4.2, 4.25, C.teal);
  s.addText("Мақсат", {
    x: 5.7, y: 1.12, w: 3.8, h: 0.42,
    fontSize: 15, fontFace: "Trebuchet MS", bold: true, color: C.text, margin: 0
  });
  const goals = [
    ["Гибридті жүйе жасау — ML + ережелер", C.teal],
    ["RU + KZ екітілді қолдау", C.teal],
    ["45 000+ мәтін деректер жиынын дайындау", C.teal],
    ["ruBert-base моделін баптау (fine-tune)", C.teal],
    ["FastAPI веб-қосымшасын іске асыру", C.teal],
  ];
  goals.forEach(([text, color], i) => {
    bullet(s, 5.7, 1.72 + i * 0.54, text, color);
  });
}

// ─── SLIDE 3 — Жүйе архитектурасы ────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "ЖҮЙЕ АРХИТЕКТУРАСЫ");

  // ML блок
  card(s, 0.35, 1.0, 4.5, 2.2, C.teal);
  s.addText("ML-модель — 60%", {
    x: 0.6, y: 1.1, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.teal, margin: 0
  });
  s.addText(
    "ruBert-base (178М параметр)\nKZ деректерінде fine-tuned\nONNX + INT8 кванттау\nИнференс: ~550 мс (CPU)",
    {
      x: 0.6, y: 1.58, w: 4.0, h: 1.5,
      fontSize: 12, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    }
  );

  // Rules блок
  card(s, 5.2, 1.0, 4.45, 2.2, C.amber);
  s.addText("Ережелер жүйесі — 40%", {
    x: 5.45, y: 1.1, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.amber, margin: 0
  });
  s.addText(
    "1. Кликбейт — 28 үлгі (RU+KZ)\n2. Лингвистика — эмоциялық лексика\n3. Дереккөз — 36 домен рейтингі\n4. Құрылым — ұзындық, деректер\n5. Фактчек — Google API",
    {
      x: 5.45, y: 1.58, w: 4.0, h: 1.5,
      fontSize: 12, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    }
  );

  // FastAPI блок
  card(s, 0.35, 3.45, 9.3, 1.8, C.mid);
  s.addText("FastAPI веб-қосымшасы — деректер ағыны", {
    x: 0.6, y: 3.55, w: 8.8, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.mid, margin: 0
  });
  const pipeline = [
    ["① Кіріс", "Мәтін немесе URL", C.teal],
    ["② Талдау", "ML + 5 ереже", C.amber],
    ["③ Скор", "Weighted 60/40", C.mid],
    ["④ Вердикт", "Толық есеп", C.green],
    ["⑤ Тарих", "SQLite сақтау", C.gray],
  ];
  pipeline.forEach(([step, desc, color], i) => {
    const px = 0.6 + i * 1.82;
    s.addShape(pres.shapes.RECTANGLE, {
      x: px, y: 4.05, w: 1.62, h: 0.9,
      fill: { color, transparency: 88 }, line: { color, width: 1.2 }
    });
    s.addText(step, {
      x: px, y: 4.1, w: 1.62, h: 0.38,
      fontSize: 11, fontFace: "Trebuchet MS", bold: true, color, align: "center", margin: 0
    });
    s.addText(desc, {
      x: px, y: 4.5, w: 1.62, h: 0.38,
      fontSize: 10, fontFace: "Calibri", color: C.text, align: "center", margin: 0
    });
  });
}

// ─── SLIDE 4 — Деректер жиыны ─────────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "ДЕРЕКТЕР ЖИЫНЫ");

  // Stat boxes top
  const stats = [
    ["45 221", "жалпы мәтін", C.teal],
    ["~35 000", "нақты жаңалықтар", C.green],
    ["~15 000", "синтетикалық дезинфо", C.red],
    ["~10 000+", "аугментация", C.amber],
  ];
  stats.forEach(([num, label, color], i) => {
    const x = 0.35 + i * 2.35;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.0, w: 2.15, h: 1.3,
      fill: { color: C.white }, line: { color: C.lightGray, width: 1 }, shadow: shadow()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.0, w: 2.15, h: 0.12,
      fill: { color }, line: { color }
    });
    s.addText(num, {
      x, y: 1.18, w: 2.15, h: 0.65,
      fontSize: 28, fontFace: "Trebuchet MS", bold: true, color, align: "center", margin: 0
    });
    s.addText(label, {
      x, y: 1.83, w: 2.15, h: 0.38,
      fontSize: 10, fontFace: "Calibri", color: C.gray, align: "center", margin: 0
    });
  });

  // Split info
  card(s, 0.35, 2.6, 4.5, 2.6, C.teal);
  s.addText("Деректер бөлінісі", {
    x: 0.6, y: 2.72, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.teal, margin: 0
  });
  s.addText(
    "Train:       31 654 мәтін  (70%)\nValidation:  6 783 мәтін  (15%)\nTest:        6 784 мәтін  (15%)\n\nСтратифицирленген бөліну\nКласс теңгерімі сақталған",
    {
      x: 0.6, y: 3.2, w: 4.0, h: 1.85,
      fontSize: 12, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    }
  );

  card(s, 5.2, 2.6, 4.45, 2.6, C.amber);
  s.addText("Дереккөздер мен тақырыптар", {
    x: 5.45, y: 2.72, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.amber, margin: 0
  });
  s.addText(
    "Нақты жаңалықтар:\ngazeta.ru · lenta.ru · ria.ru · mlsum\n\n" +
    "KZ тақырыптары (120):\nтеңге · Акорда · ҰҚК · eGov\nБайқоңыр · Арал теңізі · т.б.\n\n" +
    "Аугментация: 6 әдіс, 80% мөлшерлемесі",
    {
      x: 5.45, y: 3.2, w: 4.0, h: 1.85,
      fontSize: 12, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    }
  );
}

// ─── SLIDE 5 — Модельді оқыту ─────────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "МОДЕЛЬДІ ОҚЫТУ");

  const params = [
    ["Модель",          "ai-forever/ruBert-base (178М параметр)"],
    ["Эпохалар",        "4  (early stopping + best checkpoint)"],
    ["Learning rate",   "2e-5  (AdamW optimizer)"],
    ["Batch size",      "16 × grad_accum 2 = эффективті 32"],
    ["MAX_LENGTH",      "256 токен"],
    ["Warmup ratio",    "10%  |  Weight decay: 0.01"],
    ["Платформа",       "Google Colab T4 GPU (16 ГБ)"],
    ["Оқыту уақыты",    "~70 минут"],
  ];

  card(s, 0.35, 1.0, 5.8, 4.25, C.mid);
  s.addText("Гиперпараметрлер", {
    x: 0.6, y: 1.1, w: 5.3, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.mid, margin: 0
  });
  params.forEach(([key, val], i) => {
    s.addText(key + ":", {
      x: 0.6, y: 1.62 + i * 0.44, w: 1.6, h: 0.38,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.teal,
      align: "left", valign: "middle", margin: 0
    });
    s.addText(val, {
      x: 2.25, y: 1.62 + i * 0.44, w: 3.7, h: 0.38,
      fontSize: 11, fontFace: "Calibri", color: C.text,
      align: "left", valign: "middle", margin: 0
    });
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.55, y: 1.0, w: 3.1, h: 4.25,
    fill: { color: C.white }, line: { color: C.lightGray, width: 1 }, shadow: shadow()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.55, y: 1.0, w: 3.1, h: 0.48,
    fill: { color: C.teal, transparency: 10 }, line: { color: C.teal }
  });
  s.addText("Экспорт жолы", {
    x: 6.7, y: 1.0, w: 2.8, h: 0.48,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.white,
    align: "left", valign: "middle", margin: 0
  });
  const steps = [
    ["PyTorch", "680 МБ", C.mid],
    ["↓ ONNX", "680 МБ", C.amber],
    ["↓ INT8", "171 МБ", C.green],
  ];
  steps.forEach(([label, size, color], i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.8, y: 1.68 + i * 1.12, w: 2.7, h: 0.7,
      fill: { color, transparency: 85 }, line: { color, width: 1.5 }
    });
    s.addText(label, {
      x: 6.9, y: 1.72 + i * 1.12, w: 1.5, h: 0.62,
      fontSize: 13, fontFace: "Trebuchet MS", bold: true, color,
      align: "left", valign: "middle", margin: 0
    });
    s.addText(size, {
      x: 8.1, y: 1.72 + i * 1.12, w: 1.2, h: 0.62,
      fontSize: 12, fontFace: "Calibri", color: C.gray,
      align: "right", valign: "middle", margin: 0
    });
  });
  s.addText("4× қысу коэффициенті", {
    x: 6.8, y: 4.65, w: 2.7, h: 0.4,
    fontSize: 11, fontFace: "Calibri", color: C.green, align: "center", margin: 0
  });
}

// ─── SLIDE 6 — Нәтижелер ──────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "МОДЕЛЬ НӘТИЖЕЛЕРІ");

  const metrics = [
    ["F1-скор",    "99.9%", C.teal],
    ["Accuracy",   "99.9%", C.green],
    ["Precision",  "99.9%", C.amber],
    ["Recall",     "100%",  C.red],
  ];
  metrics.forEach(([label, val, color], i) => {
    const x = 0.35 + i * 2.35;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.0, w: 2.15, h: 1.5,
      fill: { color: C.white }, line: { color: C.lightGray, width: 1 }, shadow: shadow()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.0, w: 2.15, h: 0.14,
      fill: { color }, line: { color }
    });
    s.addText(val, {
      x, y: 1.2, w: 2.15, h: 0.8,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true, color, align: "center", margin: 0
    });
    s.addText(label, {
      x, y: 2.1, w: 2.15, h: 0.32,
      fontSize: 11, fontFace: "Calibri", color: C.gray, align: "center", margin: 0
    });
  });

  // Confusion matrix description
  card(s, 0.35, 2.75, 4.5, 2.45, C.teal);
  s.addText("Confusion Matrix", {
    x: 0.6, y: 2.87, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.teal, margin: 0
  });
  s.addText(
    "Тест жиынтығы: 6 784 мәтін\n\n" +
    "Дұрыс жіктелген: 6 778 / 6 784\n\n" +
    "Қате: тек 6 мәтін (0.09%)\n\n" +
    "Іс жүзінде мінсіз жіктеу нәтижесі",
    {
      x: 0.6, y: 3.35, w: 4.0, h: 1.7,
      fontSize: 12, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    }
  );

  card(s, 5.2, 2.75, 4.45, 2.45, C.amber);
  s.addText("Инференс жылдамдығы", {
    x: 5.45, y: 2.87, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.amber, margin: 0
  });
  s.addText(
    "Медиана:     ~550 мс (CPU)\nP95:         ~620 мс\nМодель:      INT8 кванттау\nПровайдер:   CPUExecutionProvider\n\nОрталық деплой (CPU) үшін\nжарамды жылдамдық",
    {
      x: 5.45, y: 3.35, w: 4.0, h: 1.7,
      fontSize: 12, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    }
  );
}

// ─── SLIDE 7 — Веб-қосымша ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "ВЕБ-ҚОСЫМША");

  const features = [
    ["Мәтін / URL талдау", "Тексті немесе мақала сілтемесін кіргізіп, талдауды бастаңыз", C.teal],
    ["Толық есеп", "ML-скор + 5 ереже модулі + анықталған белгілер тізімі", C.green],
    ["12 мысал", "RU + KZ тілдерінде фейк және нақты жаңалық үлгілері", C.amber],
    ["Тарих", "SQLite деректер қорында барлық талдаулар сақталады", C.mid],
    ["36 домен", "KZ медиа + халықаралық + үгіт-насихат сайттар рейтингі", C.red],
    ["Қараңғы UI", "FastAPI + HTMX + адаптивті интерфейс", C.teal],
  ];

  features.forEach(([title, desc, color], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.35 + col * 4.85;
    const y = 1.05 + row * 1.45;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.55, h: 1.25,
      fill: { color: C.white }, line: { color: C.lightGray, width: 1 }, shadow: shadow()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.12, h: 1.25,
      fill: { color }, line: { color }
    });
    s.addText(title, {
      x: x + 0.22, y: y + 0.1, w: 4.1, h: 0.4,
      fontSize: 13, fontFace: "Trebuchet MS", bold: true, color, margin: 0
    });
    s.addText(desc, {
      x: x + 0.22, y: y + 0.52, w: 4.1, h: 0.62,
      fontSize: 11, fontFace: "Calibri", color: C.text,
      align: "left", valign: "top", margin: 0
    });
  });
}

// ─── SLIDE 8 — Технологиялар стегі ────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "ТЕХНОЛОГИЯЛАР СТЕГІ");

  const groups = [
    {
      title: "Бэкенд", color: C.teal,
      items: ["Python 3.12", "FastAPI", "Uvicorn", "aiosqlite", "HTMX"]
    },
    {
      title: "ML / Инференс", color: C.mid,
      items: ["HuggingFace Transformers", "ONNX Runtime", "Optimum", "PyTorch (оқыту)"]
    },
    {
      title: "Оқыту орнытасы", color: C.amber,
      items: ["Google Colab T4 GPU", "Google Drive", "Datasets (HF)", "scikit-learn"]
    },
    {
      title: "Деректер", color: C.green,
      items: ["36 KZ/RU домен", "120 KZ тақырыбы", "6 аугментация әдісі", "45 221 мәтін"]
    },
  ];

  groups.forEach(({ title, color, items }, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.35 + col * 4.85;
    const y = 1.05 + row * 2.3;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.55, h: 2.1,
      fill: { color: C.white }, line: { color: C.lightGray, width: 1 }, shadow: shadow()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.55, h: 0.48,
      fill: { color, transparency: 10 }, line: { color }
    });
    s.addText(title, {
      x: x + 0.15, y, w: 4.2, h: 0.48,
      fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.white,
      align: "left", valign: "middle", margin: 0
    });
    items.forEach((item, j) => {
      s.addShape(pres.shapes.OVAL, {
        x: x + 0.2, y: y + 0.62 + j * 0.36, w: 0.1, h: 0.1,
        fill: { color }, line: { color }
      });
      s.addText(item, {
        x: x + 0.38, y: y + 0.56 + j * 0.36, w: 4.0, h: 0.34,
        fontSize: 12, fontFace: "Calibri", color: C.text,
        align: "left", valign: "middle", margin: 0
      });
    });
  });
}

// ─── SLIDE 9 — Шектеулер және болашақ ────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "ШЕКТЕУЛЕР ЖӘНЕ БОЛАШАҚ ЖОСПАРЛАР");

  card(s, 0.35, 1.0, 4.2, 4.25, C.red);
  s.addText("Ағымдағы шектеулер", {
    x: 0.6, y: 1.12, w: 3.8, h: 0.42,
    fontSize: 15, fontFace: "Trebuchet MS", bold: true, color: C.text, margin: 0
  });
  const limits = [
    "Тек RU + KZ тілдері — ағылшын жоқ",
    "Синтетикалық деректер — нақты KZ жаңалықтары аз",
    "CPU инференс ~550 мс — реалтайм үшін баяу",
    "URL талдауы — барлық сайт қолданылмайды",
    "Қысқа мәтін (<30 сөз) — сенімділік төмен",
  ];
  limits.forEach((text, i) => {
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: 1.72 + i * 0.52, w: 0.14, h: 0.14,
      fill: { color: C.red }, line: { color: C.red }
    });
    s.addText(text, {
      x: 0.82, y: 1.66 + i * 0.52, w: 3.6, h: 0.48,
      fontSize: 11, fontFace: "Calibri", color: C.text,
      align: "left", valign: "middle", margin: 0
    });
  });

  card(s, 5.45, 1.0, 4.2, 4.25, C.green);
  s.addText("Болашақ жоспарлар", {
    x: 5.7, y: 1.12, w: 3.8, h: 0.42,
    fontSize: 15, fontFace: "Trebuchet MS", bold: true, color: C.text, margin: 0
  });
  const plans = [
    "Нақты KZ жаңалықтарымен қайта оқыту",
    "XLM-RoBERTa — көптілді модель",
    "GPU деплой — инференсті <100 мс дейін жылдамдату",
    "БАҚ және фактчек ұйымдары үшін API",
    "Браузер плагині — тікелей тексеру",
  ];
  plans.forEach((text, i) => {
    s.addShape(pres.shapes.OVAL, {
      x: 5.7, y: 1.72 + i * 0.52, w: 0.14, h: 0.14,
      fill: { color: C.green }, line: { color: C.green }
    });
    s.addText(text, {
      x: 5.92, y: 1.66 + i * 0.52, w: 3.6, h: 0.48,
      fontSize: 11, fontFace: "Calibri", color: C.text,
      align: "left", valign: "middle", margin: 0
    });
  });
}

// ─── SLIDE 10 — Қорытынды ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  header(s, "ҚОРЫТЫНДЫ");

  const conclusions = [
    ["99.9%",   "Тест F1-скоры\nіс жүзінде мінсіз жіктеу",         C.teal],
    ["RU+KZ",   "Екітілді қолдау\nbірінші KZ дезинфо жүйесі",       C.mid],
    ["45 221",  "Мәтін деректер жиыны\nKZ-контекстік тақырыптар",    C.amber],
    ["171 МБ",  "INT8 кванттау\n4× қысу, жергілікті деплой",         C.green],
  ];
  conclusions.forEach(([num, text, color], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.35 + col * 4.85;
    const y = 1.05 + row * 2.0;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.55, h: 1.75,
      fill: { color: C.white }, line: { color: C.lightGray, width: 1 }, shadow: shadow()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.55, h: 0.12,
      fill: { color }, line: { color }
    });
    s.addText(num, {
      x, y: y + 0.18, w: 4.55, h: 0.75,
      fontSize: 38, fontFace: "Trebuchet MS", bold: true, color, align: "center", margin: 0
    });
    s.addText(text, {
      x, y: y + 0.95, w: 4.55, h: 0.65,
      fontSize: 11, fontFace: "Calibri", color: C.gray, align: "center", margin: 0
    });
  });

  s.addText("ruBert-base  ·  FastAPI  ·  ONNX  ·  Қазақстан  ·  2025", {
    x: 0.4, y: 5.2, w: 9.2, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.teal, align: "center", margin: 0
  });
}

pres.writeFile({ fileName: "/home/medet/projects/disinformation/presentation_kz.pptx" })
  .then(() => console.log("✅ presentation_kz.pptx сақталды"))
  .catch(e => console.error("❌", e));
