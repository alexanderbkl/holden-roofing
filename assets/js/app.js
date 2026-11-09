/* Holden Roofing — vanilla JS (no dependencies). */
(() => {
  "use strict";

  // Where the forms send leads. Set `endpoint` to a form service URL (e.g. Formspree) to post
  // in the background; otherwise the visitor's email app opens with the details pre-filled.
  const CONFIG = { email: "jpo@holdenroofing.com", endpoint: "" };

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  $$("[data-year]").forEach((node) => { node.textContent = new Date().getFullYear(); });

  /* Header + sticky call bar + hero parallax */
  const header = $("#header");
  const sticky = $("#sticky-cta");
  const heroMedia = $("[data-parallax]");
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    header.classList.toggle("is-scrolled", y > 24);
    if (sticky) sticky.classList.toggle("is-visible", y > 480);
    if (heroMedia && !reduceMotion && y < window.innerHeight * 1.2) {
      heroMedia.style.transform = `translate3d(0, ${y * 0.18}px, 0)`;
    }
    ticking = false;
  };
  window.addEventListener("scroll", () => {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();

  /* Mobile drawer */
  const drawer = $("#drawer");
  const burger = $(".burger");
  let lastFocus = null;
  const setDrawer = (open) => {
    drawer.classList.toggle("is-open", open);
    drawer.setAttribute("aria-hidden", String(!open));
    burger.setAttribute("aria-expanded", String(open));
    document.documentElement.style.overflow = open ? "hidden" : "";
    if (open) {
      lastFocus = document.activeElement;
      setTimeout(() => $(".drawer__close", drawer).focus(), 50);
    } else if (lastFocus) {
      lastFocus.focus();
    }
  };
  burger.addEventListener("click", () => setDrawer(true));
  $$("[data-close]", drawer).forEach((node) => node.addEventListener("click", () => setDrawer(false)));
  $$(".drawer__nav a, .drawer__foot a", drawer).forEach((link) => link.addEventListener("click", () => setDrawer(false)));
  drawer.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    const focusable = $$("a, button", drawer).filter((node) => node.offsetParent !== null);
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  window.matchMedia("(min-width: 1080px)").addEventListener("change", (event) => { if (event.matches && drawer.classList.contains("is-open")) setDrawer(false); });

  /* Scroll reveal */
  const revealItems = $$(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add("is-visible"); observer.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    revealItems.forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add("is-visible"));
  }

  /* Count-up numbers */
  const counters = $$("[data-count]");
  if (counters.length && "IntersectionObserver" in window && !reduceMotion) {
    const countObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        countObserver.unobserve(entry.target);
        const node = entry.target;
        const target = Number(node.dataset.count);
        const suffix = node.dataset.suffix || "";
        const plain = "plain" in node.dataset;
        const start = performance.now();
        const duration = 1600;
        const frame = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - t, 4);
          const value = Math.round(target * eased);
          node.textContent = (plain ? String(value) : value.toLocaleString("en-US")) + (t === 1 ? suffix : "");
          if (t < 1) requestAnimationFrame(frame);
        };
        requestAnimationFrame(frame);
      });
    }, { threshold: 0.6 });
    counters.forEach((node) => countObserver.observe(node));
  }

  /* Materials tabs */
  $$(".tablist").forEach((list) => {
    const tabs = $$('[role="tab"]', list);
    const media = $(".materials__media");
    const select = (tab, focus) => {
      tabs.forEach((other) => {
        const on = other === tab;
        other.setAttribute("aria-selected", String(on));
        other.tabIndex = on ? 0 : -1;
        const panel = document.getElementById(other.getAttribute("aria-controls"));
        panel.hidden = !on;
        panel.classList.toggle("is-active", on);
        if (on && media) $$("img", media).forEach((img) => img.classList.toggle("is-active", img.dataset.for === panel.dataset.img));
      });
      if (focus) tab.focus();
    };
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => select(tab));
      tab.addEventListener("keydown", (event) => {
        const move = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
        if (move) { event.preventDefault(); select(tabs[(index + move + tabs.length) % tabs.length], true); }
        if (event.key === "Home") { event.preventDefault(); select(tabs[0], true); }
        if (event.key === "End") { event.preventDefault(); select(tabs[tabs.length - 1], true); }
      });
    });
  });

  /* Reviews carousel */
  $$("[data-carousel]").forEach((track) => {
    const root = track.closest("section") || document;
    const prev = $("[data-prev]", root);
    const next = $("[data-next]", root);
    const step = () => (track.firstElementChild ? track.firstElementChild.getBoundingClientRect().width + 20 : 320);
    const update = () => {
      if (prev) prev.disabled = track.scrollLeft < 8;
      if (next) next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 8;
    };
    if (prev) prev.addEventListener("click", () => track.scrollBy({ left: -step(), behavior: "smooth" }));
    if (next) next.addEventListener("click", () => track.scrollBy({ left: step(), behavior: "smooth" }));
    track.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
    track.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight") track.scrollBy({ left: step(), behavior: "smooth" });
      if (event.key === "ArrowLeft") track.scrollBy({ left: -step(), behavior: "smooth" });
    });
    window.addEventListener("resize", update);
    update();
  });

  /* Lightbox */
  const lightbox = $("#lightbox");
  const items = $$(".gallery__item");
  if (lightbox && items.length) {
    const image = $("img", lightbox);
    const caption = $("figcaption", lightbox);
    let index = 0;
    let opener = null;
    const show = (i) => {
      index = (i + items.length) % items.length;
      const item = items[index];
      image.src = item.dataset.full;
      image.alt = $("img", item).alt;
      caption.textContent = item.dataset.caption || "";
    };
    const open = (i, trigger) => {
      opener = trigger;
      show(i);
      lightbox.classList.add("is-open");
      lightbox.setAttribute("aria-hidden", "false");
      document.documentElement.style.overflow = "hidden";
      $(".lb-close", lightbox).focus();
    };
    const close = () => {
      lightbox.classList.remove("is-open");
      lightbox.setAttribute("aria-hidden", "true");
      document.documentElement.style.overflow = "";
      if (opener) opener.focus();
    };
    items.forEach((item, i) => item.addEventListener("click", () => open(i, item)));
    $(".lb-close", lightbox).addEventListener("click", close);
    $(".lb-prev", lightbox).addEventListener("click", () => show(index - 1));
    $(".lb-next", lightbox).addEventListener("click", () => show(index + 1));
    lightbox.addEventListener("click", (event) => { if (event.target === lightbox) close(); });
    document.addEventListener("keydown", (event) => {
      if (!lightbox.classList.contains("is-open")) return;
      if (event.key === "Escape") close();
      if (event.key === "ArrowLeft") show(index - 1);
      if (event.key === "ArrowRight") show(index + 1);
    });
    let startX = 0;
    lightbox.addEventListener("touchstart", (event) => { startX = event.touches[0].clientX; }, { passive: true });
    lightbox.addEventListener("touchend", (event) => {
      const dx = event.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
    });
  }

  /* Financing estimator (9.99% APR, 120 months) */
  $$("[data-estimator]").forEach((root) => {
    const range = $("input[type=range]", root);
    const amount = $("[data-amount]", root);
    const pay = $("[data-pay]", root);
    const total = $("[data-total]", root);
    const monthly = (principal) => {
      const r = 0.0999 / 12;
      return (principal * r) / (1 - Math.pow(1 + r, -120));
    };
    const money = (value, digits = 0) => "$" + value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    const update = () => {
      const value = Number(range.value);
      const payment = Math.round(monthly(value) * 100) / 100;
      amount.textContent = money(value);
      pay.textContent = payment.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      total.textContent = money(payment * 120, 2);
      range.style.setProperty("--p", ((value - range.min) / (range.max - range.min)) * 100 + "%");
    };
    range.addEventListener("input", update);
    update();
  });

  /* Office locator: map pins + tabs + lazy Google Maps embed */
  const locator = $(".locator");
  if (locator) {
    const pins = $$(".map__pin", locator);
    const tabs = $$(".office-tab", locator);
    const panels = $$(".office", locator);
    let current = panels[0] ? panels[0].dataset.office : null;
    let mapsLive = false;

    const loadMap = (panel) => {
      const holder = $("[data-map]", panel);
      if (!mapsLive || !holder || holder.dataset.loaded) return;
      holder.dataset.loaded = "1";
      const frame = document.createElement("iframe");
      frame.src = `https://www.google.com/maps?q=${panel.dataset.query}&output=embed`;
      frame.title = `Map of ${$("h3", panel).textContent}`;
      frame.loading = "lazy";
      frame.referrerPolicy = "no-referrer-when-downgrade";
      frame.addEventListener("load", () => { holder.style.animation = "none"; });
      holder.appendChild(frame);
    };
    const select = (key, focusTab) => {
      current = key;
      pins.forEach((pin) => pin.classList.toggle("is-active", pin.dataset.office === key));
      tabs.forEach((tab) => {
        const on = tab.dataset.office === key;
        tab.setAttribute("aria-selected", String(on));
        tab.tabIndex = on ? 0 : -1;
        if (on && focusTab) tab.focus();
      });
      panels.forEach((panel) => {
        const on = panel.dataset.office === key;
        panel.classList.toggle("is-active", on);
        if (on) loadMap(panel);
      });
    };
    pins.forEach((pin) => {
      pin.addEventListener("click", () => select(pin.dataset.office));
      pin.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); select(pin.dataset.office); }
      });
    });
    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => select(tab.dataset.office));
      tab.addEventListener("keydown", (event) => {
        const move = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
        if (move) { event.preventDefault(); select(tabs[(i + move + tabs.length) % tabs.length].dataset.office, true); }
      });
    });
    const hash = location.hash.match(/^#office-([\w-]+)/);
    if (hash && tabs.some((tab) => tab.dataset.office === hash[1])) select(hash[1]);
    else select(current);
    window.addEventListener("hashchange", () => {
      const m = location.hash.match(/^#office-([\w-]+)/);
      if (m) select(m[1]);
    });

    if ("IntersectionObserver" in window) {
      const mapObserver = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          mapsLive = true;
          panels.filter((panel) => panel.classList.contains("is-active")).forEach(loadMap);
          mapObserver.disconnect();
        }
      }, { rootMargin: "200px" });
      mapObserver.observe(locator);
    } else {
      mapsLive = true;
      panels.filter((panel) => panel.classList.contains("is-active")).forEach(loadMap);
    }
  }

  /* FAQ: keep one answer open at a time */
  $$(".faq").forEach((faq) => {
    const all = $$("details", faq);
    all.forEach((detail) => detail.addEventListener("toggle", () => {
      if (detail.open) all.forEach((other) => { if (other !== detail) other.open = false; });
    }));
  });

  /* Lead forms */
  const formatPhone = (value) => {
    const d = value.replace(/\D/g, "").slice(0, 10);
    if (d.length < 4) return d;
    if (d.length < 7) return `(${d.slice(0, 3)}) ${d.slice(3)}`;
    return `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}`;
  };
  $$("form[data-quote-form]").forEach((form) => {
    const status = $("[data-status]", form);
    const phone = $("input[name=phone]", form);
    const params = new URLSearchParams(location.search);
    const preset = params.get("service");
    if (preset) {
      $$("input[name=service]", form).forEach((input) => {
        if (input.value.toLowerCase().includes(preset.toLowerCase())) input.checked = true;
      });
    }
    if (phone) phone.addEventListener("input", () => { phone.value = formatPhone(phone.value); });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      const data = new FormData(form);
      if (data.get("company")) return;
      const fields = {
        Name: data.get("name"), Phone: data.get("phone"), ZIP: data.get("zip"), Email: data.get("email") || "—",
        Service: data.get("service"), Office: data.get("office") || "No preference", Message: data.get("message") || "—",
      };
      const show = (message) => { status.textContent = message; status.classList.add("is-shown"); };
      if (CONFIG.endpoint) {
        try {
          const response = await fetch(CONFIG.endpoint, { method: "POST", body: data, headers: { Accept: "application/json" } });
          if (!response.ok) throw new Error(response.statusText);
          form.reset();
          show("Thank you! A Holden Roofing specialist will call you shortly.");
        } catch (error) {
          show("Something went wrong. Please call us at 888.553.1318.");
        }
        return;
      }
      const body = Object.entries(fields).map(([key, value]) => `${key}: ${value}`).join("\n");
      const subject = `Free roof inspection request — ${fields.Name}`;
      window.location.href = `mailto:${CONFIG.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      show("Opening your email app with your details filled in. Prefer to talk? Call 888.553.1318.");
    });
  });
})();
