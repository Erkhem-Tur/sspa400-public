(function (global) {
  "use strict";

  const support = (mn, keywords, frame) => ({ mn, keywords, frame });

  global.TRANSLANGUAGING_SUPPORT = [
    support(
      "Энэ хичээлээр сайжруулах нэг чадвараа эхлээд Монгол хэлээр тодорхойлоод, дараа нь English goal болгон бич.",
      ["employment", "policy", "point of view", "summary"],
      "In this lesson, I want to improve ___ because ___."
    ),
    support(
      "Preview дээрх үг, дүрэм, харилцааны зорилгыг Монгол хэлээр 3 ангилаад English түлхүүр үг сонго.",
      ["vocabulary", "grammar", "function", "skill"],
      "This lesson helps me talk about ___ and use ___."
    ),
    support(
      "Ажил хайх үе шатыг Монгол хэлээр дарааллуул. Дараа нь үе шат бүрийг English үйл үгээр нэрлэ.",
      ["search", "apply", "interview", "hire"],
      "First, a job seeker should ___. Then, they should ___."
    ),
    support(
      "Өгүүлбэрийн гол санааг Монгол хэлээр шалгаад T/F шийд. False бол буруу хэсгийг English-ээр зас.",
      ["true", "false", "correct", "job search"],
      "The statement is false because ___. The correct information is ___."
    ),
    support(
      "Training dialog-ийн чухал мэдээллийг Монгол хэлээр товч тэмдэглээд, English complete sentence болгон хувирга.",
      ["training", "employee", "message", "schedule"],
      "The new employee needs to know that ___."
    ),
    support(
      "Асуултын зорилгыг Монгол хэлээр тайлбарла: батлах, гайхах/дургүйцэх, эсвэл мэдээлэл асуух. Дараа нь English хэлбэрийг бич.",
      ["negative question", "auxiliary", "subject", "purpose"],
      "___n’t + subject + base verb/complement?"
    ),
    support(
      "Эх өгүүлбэрийн tense болон auxiliary-г Монгол хэлээр нэрлээд, auxiliary-г negative болгон өгүүлбэрийн эхэнд шилжүүл.",
      ["doesn’t", "couldn’t", "hasn’t", "won’t"],
      "Statement: ___. Negative question: ___n’t + subject + ___?"
    ),
    support(
      "Speaker яагаад negative question хэрэглэснийг Монгол хэлээр шийдээд A, S/A, эсвэл I кодыг сонго.",
      ["agreement", "surprise", "annoyance", "information"],
      "The speaker is using the question to show/ask for ___."
    ),
    support(
      "Хариуныхаа санааг Монгол хэлээр 10 секунд бод. Дараа нь English negative question болон богино reason ашиглан partner-тэй ярь.",
      ["don’t", "didn’t", "isn’t", "why"],
      "Don’t/Didn’t/Isn’t ___? I think ___ because ___."
    ),
    support(
      "Benefit болон policy-ийн ялгааг Монгол хэлээр нэг өгүүлбэрээр тайлбарлаад, жишээнүүдийг English-ээр хоёр ангил.",
      ["benefit", "policy", "permitted", "required"],
      "___ is a benefit, while ___ is a company policy."
    ),
    support(
      "Word box-ийн үг бүрийн Монгол утгыг түр санаж, өгүүлбэрт ямар part of speech хэрэгтэйг English sentence-ээс шийд.",
      ["hire", "employment", "permitted", "definite"],
      "The context needs a ___, so the best word is ___."
    ),
    support(
      "Нөхцөл яагаад боломжгүйг Монгол хэлээр тайлбарла. Дараа нь can’t be/couldn’t be + English reason болгон хэл.",
      ["can’t be", "couldn’t be", "evidence", "reason"],
      "It can’t/couldn’t be ___ because ___."
    ),
    support(
      "Эхлээд нотолгоогоо Монгол хэлээр ол. Дараа нь logical impossibility-г English response + because reason хэлбэрээр бич.",
      ["impossible", "unlikely", "because", "evidence"],
      "That can’t be true because ___."
    ),
    support(
      "Diagram-ийн харилцааг Монгол хэлээр уншаад, team/player/result гэсэн English нэр томьёогоор хариул.",
      ["tournament", "team", "result", "advance"],
      "According to the diagram, ___ because ___."
    ),
    support(
      "E-mail бүрийн гол санааг Монгол хэлээр 5–7 үгээр тэмдэглээд, professional English sentence болгон бич.",
      ["professional", "purpose", "request", "response"],
      "The purpose of this message is to ___."
    ),
    support(
      "Үгийн Монгол утгыг шалгасны дараа professional context-д тохирох English option-ийг сонго.",
      ["professional", "appropriate", "concern", "convince"],
      "In this context, ___ means ___."
    ),
    support(
      "Susan, Tom хоёрын байр суурийг Монгол хэлээр тус тус нэг өгүүлбэрээр тоймлоод English claim болгон хувирга.",
      ["point of view", "agree", "disagree", "opinion"],
      "Susan believes ___, whereas Tom believes ___."
    ),
    support(
      "Statement бүрийг Монгол хэлээр paraphrase хийгээд хэний санаа болохыг source text-ээс нотол.",
      ["Susan", "Tom", "neither", "both"],
      "This statement belongs to ___ because the text says ___."
    ),
    support(
      "Сонголт бүрийн Монгол утгыг түр хэлээд, эх өгүүлбэртэй утга ба grammar хоёроор нь тулга.",
      ["meaning", "context", "choice", "evidence"],
      "Choice ___ fits because it means ___."
    ),
    support(
      "Нэг язгуур үгийн Монгол үндсэн утгыг хадгалаад, sentence position-оос English part of speech-ийг шийд.",
      ["employ", "employee", "employer", "employment"],
      "The sentence needs a noun/verb/adjective/adverb, so I use ___."
    ),
    support(
      "Word family-г Монгол утгаар нь нэг бүлэг гэж хар. Дараа нь suffix болон singular/plural-ийг English grammar-аар зөв сонго.",
      ["agreement", "supervise", "definitely", "unemployment"],
      "The correct related form is ___ because the blank needs a ___."
    ),
    support(
      "Саналынхаа гол шалтгааныг Монгол хэлээр бодоод, stance + reason + example гэсэн English бүтэц ашиглан ярь.",
      ["strongly agree", "agree", "disagree", "reason"],
      "I agree/disagree because ___. For example, ___."
    ),
    support(
      "Tag question-ийн зорилгыг Монгол хэлээр шийд: батлуулах уу, үнэхээр асууж байна уу? Дараа нь voice-оо falling/rising болго.",
      ["tag question", "falling", "rising", "confirmation"],
      "You agree, don’t you? ↘ / You haven’t seen it, have you? ↗"
    ),
    support(
      "Adjective-ийн Монгол утгыг хадгалаад, чанар/байдлыг нэрлэсэн English noun хэрэгтэй бол -ness залга.",
      ["adjective", "noun", "-ness", "quality"],
      "___ is an adjective; the noun for that quality is ___."
    ),
    support(
      "Blank-д үйл үг үү, нэр үг үү хэрэгтэйг Монгол хэлээр тодорхойлоод -ness эсвэл -ment form сонго.",
      ["-ness", "-ment", "noun", "verb"],
      "The sentence needs a noun, so ___ becomes ___."
    ),
    support(
      "Үйлдлийн Монгол утгыг эхлээд тодорхойл. Дараа нь result/process гэсэн noun хэрэгтэй бол зөв -ment form бич.",
      ["appointment", "employment", "argument", "requirement"],
      "The verb is ___; the related -ment noun is ___."
    ),
    support(
      "Past robots, Both, Today’s robots гэсэн 3 хэсэгт санаагаа Монгол хэлээр ангилаад English key phrases болгон map-д оруул.",
      ["past", "both", "today", "similarity", "difference"],
      "Past robots ___. Both types ___. Today’s robots ___."
    ),
    support(
      "Эхлээд main idea болон 2–3 detail-аа Монгол хэлээр төлөвлө. Дараа нь opinion нэмэхгүйгээр English summary болгон холбо.",
      ["main idea", "key detail", "in contrast", "overall"],
      "The text explains ___. In the past, ___. Today, ___. Overall, ___."
    )
  ];
})(window);
