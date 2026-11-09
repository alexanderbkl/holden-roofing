/* Robinson & Sons Roofing & Remodeling — vanilla JS (no dependencies) */
(() => {
  "use strict";

  // Set to a form backend URL (e.g. Formspree/Getform) to receive quote requests by email.
  const FORM_ENDPOINT = "";

  const CITIES = {
    "austin": { name: "Austin", phone: "(512) 580-7400", tel: "+15125807400", zip: "78741", radius: 48, label: "right" },
    "san-antonio": { name: "San Antonio", phone: "(726) 215-8800", tel: "+17262158800", zip: "78254", radius: 66, label: "left" },
    "arlington": { name: "Arlington", phone: "(469) 290-1120", tel: "+14692901120", zip: "76017", radius: 60, label: "right" },
    "houston": { name: "Houston", phone: "(936) 280-4222", tel: "+19362804222", zip: "77080", radius: 42, label: "right" },
  };
  const HOURS = { 0: [9, 15], 1: [8, 18], 2: [8, 18], 3: [8, 18], 4: [8, 18], 5: [8, 18], 6: [9, 15] };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.documentElement.classList.add("js");

  /* ---------- City state ---------- */
  let city = "austin";
  try {
    const saved = localStorage.getItem("robinson-city");
    if (CITIES[saved]) city = saved;
  } catch (_) { /* storage unavailable */ }

  const mapApi = { select: () => {} };

  function setCity(key) {
    if (!CITIES[key]) return;
    city = key;
    const data = CITIES[key];
    try { localStorage.setItem("robinson-city", key); } catch (_) { /* ignore */ }
    $$("[data-phone-link]").forEach((el) => { el.href = `tel:${data.tel}`; });
    $$("[data-phone-text]").forEach((el) => { el.textContent = data.phone; });
    $$("[data-city-name]").forEach((el) => { el.textContent = data.name; });
    $$(".chip[data-city]").forEach((chip) => chip.setAttribute("aria-pressed", String(chip.dataset.city === key)));
    const select = $("#f-city");
    if (select) select.value = key;
    mapApi.select(key);
  }

  $$(".chip[data-city]").forEach((chip) => chip.addEventListener("click", () => setCity(chip.dataset.city)));
  $("#f-city")?.addEventListener("change", (event) => setCity(event.target.value));

  /* ---------- Open-now status (Central Time) ---------- */
  function updateStatus() {
    const el = $("#openStatus");
    if (!el) return;
    const parts = new Intl.DateTimeFormat("en-US", { timeZone: "America/Chicago", weekday: "short", hour: "numeric", minute: "numeric", hourCycle: "h23" }).formatToParts(new Date());
    const get = (type) => parts.find((p) => p.type === type).value;
    const day = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(get("weekday"));
    const hour = Number(get("hour")) + Number(get("minute")) / 60;
    const [open, close] = HOURS[day];
    const fmt = (h) => `${h % 12 || 12} ${h < 12 ? "AM" : "PM"}`;
    const box = el.closest(".status");
    if (hour >= open && hour < close) {
      el.textContent = `Open now · until ${fmt(close)} CT`;
      box.classList.remove("is-closed");
    } else {
      el.textContent = "Closed now · same-day & next-day bookings";
      box.classList.add("is-closed");
    }
  }

  /* ---------- Header, mobile bar, parallax ---------- */
  const header = $(".site-header");
  const bar = $(".mobile-bar");
  const hero = $(".hero");
  const parallax = $("[data-parallax]");
  let ticking = false;

  function onScroll() {
    const y = window.scrollY;
    header.classList.toggle("is-scrolled", y > 24);
    if (bar && hero) bar.classList.toggle("is-visible", y > hero.offsetHeight * 0.6);
    if (parallax && !reduceMotion) {
      const rect = parallax.parentElement.getBoundingClientRect();
      if (rect.bottom > 0 && rect.top < innerHeight) {
        parallax.style.transform = `translateY(${(rect.top - innerHeight / 2) * -0.12}px)`;
      }
    }
    ticking = false;
  }
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });

  /* ---------- Mobile drawer ---------- */
  const drawer = $("#drawer");
  const backdrop = $("#backdrop");
  const menuBtn = $("#menuBtn");
  let lastFocus = null;

  function setDrawer(open) {
    if (open) lastFocus = document.activeElement;
    drawer.classList.toggle("is-open", open);
    drawer.setAttribute("aria-hidden", String(!open));
    drawer.inert = !open;
    menuBtn.setAttribute("aria-expanded", String(open));
    document.body.style.overflow = open ? "hidden" : "";
    if (open) {
      backdrop.hidden = false;
      requestAnimationFrame(() => backdrop.classList.add("is-open"));
      $("#drawerClose").focus();
    } else {
      backdrop.classList.remove("is-open");
      setTimeout(() => { if (!drawer.classList.contains("is-open")) backdrop.hidden = true; }, 300);
      lastFocus?.focus?.();
    }
  }
  menuBtn.addEventListener("click", () => setDrawer(!drawer.classList.contains("is-open")));
  $("#drawerClose").addEventListener("click", () => setDrawer(false));
  backdrop.addEventListener("click", () => setDrawer(false));
  drawer.addEventListener("click", (event) => { if (event.target.closest("a")) setDrawer(false); });
  addEventListener("keydown", (event) => { if (event.key === "Escape" && drawer.classList.contains("is-open")) setDrawer(false); });
  matchMedia("(min-width: 960px)").addEventListener("change", (m) => { if (m.matches && drawer.classList.contains("is-open")) setDrawer(false); });

  /* ---------- Scroll reveal ---------- */
  const revealEls = $$(".reveal");
  revealEls.forEach((el) => {
    const siblings = [...el.parentElement.children].filter((c) => c.classList.contains("reveal"));
    el.style.setProperty("--d", `${Math.min(siblings.indexOf(el), 6) * 70}ms`);
  });
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add("is-in"); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-in"));
  }

  /* ---------- Roof type tabs ---------- */
  const tabs = $$('[role="tab"]');
  function selectTab(tab, focus = false) {
    tabs.forEach((t) => {
      const active = t === tab;
      t.setAttribute("aria-selected", String(active));
      t.tabIndex = active ? 0 : -1;
      $(`#${t.getAttribute("aria-controls")}`).hidden = !active;
    });
    if (focus) tab.focus();
    tab.scrollIntoView?.({ block: "nearest", inline: "center", behavior: reduceMotion ? "auto" : "smooth" });
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => selectTab(tab));
    tab.addEventListener("keydown", (event) => {
      const keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (event.key in keys) { event.preventDefault(); selectTab(tabs[(i + keys[event.key] + tabs.length) % tabs.length], true); }
      if (event.key === "Home") { event.preventDefault(); selectTab(tabs[0], true); }
      if (event.key === "End") { event.preventDefault(); selectTab(tabs[tabs.length - 1], true); }
    });
  });

  /* ---------- All-services toggle ---------- */
  const toggleAll = $("#toggleAll");
  const allList = $("#allList");
  toggleAll?.addEventListener("click", () => {
    const open = allList.hidden;
    allList.hidden = !open;
    toggleAll.setAttribute("aria-expanded", String(open));
    toggleAll.firstChild.textContent = open ? "Hide full list " : "View all 25 services ";
    $$("li", allList).forEach((li, i) => { li.style.animationDelay = `${i * 18}ms`; });
  });

  // Service cards preselect the matching option in the quote form.
  $$("[data-service]").forEach((link) => link.addEventListener("click", () => {
    const select = $("#f-service");
    if ([...select.options].some((o) => o.value === link.dataset.service || o.textContent === link.dataset.service)) select.value = link.dataset.service;
  }));

  /* ---------- Texas map ---------- */
  const TEXAS = [
    [-103.04, 36.5], [-100.0, 36.5], [-100.0, 34.56], [-99.2, 34.21], [-98.1, 34.15], [-97.2, 33.85], [-96.6, 33.84],
    [-95.5, 33.88], [-94.5, 33.65], [-94.04, 33.55], [-94.04, 31.99], [-93.52, 31.18], [-93.7, 30.3], [-93.85, 29.7],
    [-94.7, 29.35], [-95.5, 28.9], [-96.4, 28.35], [-97.0, 27.8], [-97.4, 27.0], [-97.2, 26.0], [-97.15, 25.95],
    [-98.3, 26.1], [-99.1, 26.4], [-99.5, 27.5], [-100.3, 28.3], [-101.0, 29.4], [-102.4, 29.8], [-102.7, 29.7],
    [-103.1, 29.0], [-104.0, 29.3], [-104.7, 30.1], [-105.0, 30.7], [-106.6, 31.8], [-106.6, 32.0], [-103.06, 32.0],
  ];
  const SCALE = 40;
  const project = (lon, lat) => [(lon + 106.7) * 0.857 * SCALE + 24, (36.6 - lat) * SCALE + 8];

  function initMap() {
    const svg = $("#txMap");
    if (!svg) return;
    const NS = "http://www.w3.org/2000/svg";
    const make = (tag, attrs = {}, parent = svg) => {
      const el = document.createElementNS(NS, tag);
      Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
      parent.appendChild(el);
      return el;
    };
    for (let lat = 26; lat <= 36; lat += 2) {
      const y = project(-100, lat)[1];
      make("line", { class: "tx-grid", x1: 0, x2: 500, y1: y, y2: y });
    }
    for (let lon = -106; lon <= -94; lon += 2) {
      const x = project(lon, 30)[0];
      make("line", { class: "tx-grid", x1: x, x2: x, y1: 0, y2: 450 });
    }
    make("path", { class: "tx-shape", d: `M${TEXAS.map(([lon, lat]) => project(lon, lat).map((n) => n.toFixed(1)).join(",")).join("L")}Z` });
    const radiusCircle = make("circle", { class: "tx-radius", r: 0 });
    const pins = {};
    $$(".loc[data-city]").forEach((card) => {
      const key = card.dataset.city;
      const [x, y] = project(Number(card.dataset.lon), Number(card.dataset.lat));
      const group = make("g", { class: "pin", tabindex: 0, role: "button", "aria-label": `Show ${CITIES[key].name} service area` });
      make("circle", { class: "pin-ring", cx: x, cy: y, r: 10 }, group);
      make("circle", { class: "pin-dot", cx: x, cy: y, r: 7.5 }, group);
      const left = CITIES[key].label === "left";
      const text = make("text", { x: x + (left ? -15 : 15), y: y + 5, "text-anchor": left ? "end" : "start" }, group);
      text.textContent = CITIES[key].name;
      group.addEventListener("click", () => setCity(key));
      group.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setCity(key); } });
      pins[key] = { group, x, y };
    });

    mapApi.select = (key) => {
      const pin = pins[key];
      if (!pin) return;
      Object.entries(pins).forEach(([k, p]) => p.group.classList.toggle("is-active", k === key));
      $$(".loc").forEach((card) => card.classList.toggle("is-active", card.dataset.city === key));
      const miles = CITIES[key].radius;
      radiusCircle.setAttribute("cx", pin.x);
      radiusCircle.setAttribute("cy", pin.y);
      radiusCircle.setAttribute("r", (miles / 69) * SCALE);
      pin.group.parentNode.appendChild(pin.group);
      $("#mapNote").textContent = `${CITIES[key].name} service range: about ${miles} miles around ZIP ${CITIES[key].zip}`;
    };
    $$(".loc[data-city]").forEach((card) => {
      card.addEventListener("click", (event) => { if (!event.target.closest("a")) setCity(card.dataset.city); });
      card.addEventListener("keydown", (event) => { if (event.key === "Enter" && event.target === card) setCity(card.dataset.city); });
    });
  }

  /* ---------- Quote form ---------- */
  const form = $("#quoteForm");
  const status = $("#formStatus");
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

  function validate() {
    let valid = true;
    $$("[required]", form).forEach((field) => {
      let ok = field.value.trim() !== "";
      if (ok && field.type === "email") ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value);
      if (ok && field.type === "tel") ok = field.value.replace(/\D/g, "").length >= 10;
      field.closest(".field").classList.toggle("has-error", !ok);
      field.setAttribute("aria-invalid", String(!ok));
      if (!ok && valid) field.focus();
      valid = valid && ok;
    });
    return valid;
  }

  form?.addEventListener("input", (event) => event.target.closest(".field")?.classList.remove("has-error"));
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.className = "form-status";
    if (form.company.value) return; // honeypot
    if (!validate()) { status.textContent = "Please complete the highlighted fields."; status.classList.add("err"); return; }

    const data = Object.fromEntries(new FormData(form));
    const target = CITIES[data.city] || CITIES[city];
    const button = $("button[type=submit]", form);
    button.disabled = true;

    try {
      if (FORM_ENDPOINT) {
        const response = await fetch(FORM_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(data) });
        if (!response.ok) throw new Error("Request failed");
        status.textContent = `Thanks, ${data.name.split(" ")[0]}! Your ${target.name} team will contact you shortly.`;
        status.classList.add("ok");
        form.reset();
        setCity(data.city);
      } else {
        const body = `Hi Robinson & Sons, I need a quote.\nService: ${data.service}\nCity: ${target.name}\nName: ${data.name}\nPhone: ${data.phone}\n${data.message || ""}`;
        status.textContent = `Thanks, ${data.name.split(" ")[0]}! For the fastest reply, call ${target.name} at ${target.phone}.`;
        status.classList.add("ok");
        if (isMobile) location.href = `sms:${target.tel}?&body=${encodeURIComponent(body)}`;
      }
    } catch (_) {
      status.textContent = `Something went wrong. Please call ${target.name} at ${target.phone}.`;
      status.classList.add("err");
    } finally {
      button.disabled = false;
    }
  });

  /* ---------- Init ---------- */
  const year = $("#year");
  if (year) year.textContent = new Date().getFullYear();
  initMap();
  setCity(city);
  updateStatus();
  setInterval(updateStatus, 60000);
  onScroll();
})();
