const sourceLanguage = "zh-CN";
const languageSelect = document.querySelector("#language-select");
const paperList = document.querySelector("#paper-list");
const paperMeta = document.querySelector("#paper-meta");

function expireGoogleTranslateCookie(domain) {
  const domainPart = domain ? `; domain=${domain}` : "";
  document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/${domainPart}`;
}

function clearGoogleTranslateCookies() {
  expireGoogleTranslateCookie();

  if (location.hostname) {
    expireGoogleTranslateCookie(location.hostname);
    expireGoogleTranslateCookie(`.${location.hostname}`);
  }
}

function getCookieLanguage() {
  const match = document.cookie.match(/(?:^|; )googtrans=\/[^/]+\/([^;]+)/);
  return match ? decodeURIComponent(match[1]) : sourceLanguage;
}

function getStoredLanguage() {
  const storedLanguage = localStorage.getItem("homepage-language");
  const availableLanguages = Array.from(languageSelect.options).map((option) => option.value);

  if (storedLanguage && availableLanguages.includes(storedLanguage)) {
    return storedLanguage;
  }

  const cookieLanguage = getCookieLanguage();
  return availableLanguages.includes(cookieLanguage) ? cookieLanguage : sourceLanguage;
}

function applyGoogleTranslation(language, retries = 30) {
  const googleCombo = document.querySelector(".goog-te-combo");

  if (!googleCombo) {
    if (retries > 0) {
      window.setTimeout(() => applyGoogleTranslation(language, retries - 1), 250);
    }

    return;
  }

  googleCombo.value = language;
  googleCombo.dispatchEvent(new Event("change"));
}

function setLanguage(language) {
  localStorage.setItem("homepage-language", language);
  languageSelect.value = language;

  if (language === sourceLanguage) {
    clearGoogleTranslateCookies();
    window.location.reload();
    return;
  }

  applyGoogleTranslation(language);
}

languageSelect.value = getStoredLanguage();
languageSelect.addEventListener("change", (event) => setLanguage(event.target.value));

window.addEventListener("load", () => {
  document.body.classList.add("translation-ready");

  if (languageSelect.value !== sourceLanguage) {
    applyGoogleTranslation(languageSelect.value);
  }
});

function formatDate(dateValue) {
  if (!dateValue) {
    return "日期待确认";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date(dateValue));
}

function createPaperCard(paper) {
  const card = document.createElement("article");
  card.className = "paper-card";

  const title = document.createElement("h3");
  const link = document.createElement(paper.url ? "a" : "span");
  link.textContent = paper.title;

  if (paper.url) {
    link.href = paper.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }

  title.append(link);

  const details = document.createElement("p");
  details.className = "paper-details";
  details.textContent = [
    paper.authors?.join(", "),
    paper.journal,
    paper.published ? formatDate(paper.published) : "",
    paper.quartile
  ].filter(Boolean).join(" · ");

  const tags = document.createElement("div");
  tags.className = "paper-tags";

  for (const keyword of paper.keywords || []) {
    const tag = document.createElement("span");
    tag.textContent = keyword;
    tags.append(tag);
  }

  if (paper.doi) {
    const doi = document.createElement("span");
    doi.textContent = `DOI: ${paper.doi}`;
    tags.append(doi);
  }

  card.append(title, details, tags);
  return card;
}

function renderPaperData(data) {
  const papers = data.papers || [];
  const generatedDate = data.generated_at ? formatDate(data.generated_at) : "尚未生成";

  paperMeta.textContent = `数据源：${data.source || "Crossref"} · 更新时间：${generatedDate} · 共 ${papers.length} 篇`;
  paperList.replaceChildren();

  if (!papers.length) {
    const empty = document.createElement("article");
    empty.className = "paper-empty";
    empty.innerHTML = "<h3>暂无匹配论文</h3><p>自动任务运行后，如果近 3 年内匹配到白名单 Transactions 论文，会显示在这里。</p>";
    paperList.append(empty);
    return;
  }

  for (const paper of papers.slice(0, 30)) {
    paperList.append(createPaperCard(paper));
  }
}

async function loadPaperData() {
  if (!paperList || !paperMeta) {
    return;
  }

  try {
    const response = await fetch(`data/papers.json?v=${Date.now()}`);

    if (!response.ok) {
      throw new Error(`Paper data request failed: ${response.status}`);
    }

    renderPaperData(await response.json());
  } catch (error) {
    paperMeta.textContent = "论文数据暂时无法读取。";
    paperList.replaceChildren();

    const empty = document.createElement("article");
    empty.className = "paper-empty";
    empty.innerHTML = "<h3>读取失败</h3><p>请确认 data/papers.json 已提交，并等待 GitHub Pages 完成部署。</p>";
    paperList.append(empty);
  }
}

loadPaperData();
