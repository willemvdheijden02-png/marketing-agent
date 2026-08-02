/* =========================================================
   8eonAI — interactie
   GSAP + ScrollTrigger + Lenis worden via CDN geladen (zie <head>).
   Alles degradeert netjes als een lib niet laadt.
   ========================================================= */

(function () {
	"use strict";

	var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

	/* ---------- Smooth scroll (Lenis) ---------- */
	function initLenis() {
		if (reduceMotion || typeof Lenis === "undefined") return;

		var lenis = new Lenis({ duration: 1.05, smoothWheel: true });

		function raf(time) {
			lenis.raf(time);
			requestAnimationFrame(raf);
		}
		requestAnimationFrame(raf);

		if (typeof ScrollTrigger !== "undefined") {
			lenis.on("scroll", ScrollTrigger.update);
		}

		// Ankerlinks door Lenis laten lopen
		document.querySelectorAll('a[href^="#"]').forEach(function (a) {
			a.addEventListener("click", function (e) {
				var id = a.getAttribute("href");
				if (id.length < 2) return;
				var target = document.querySelector(id);
				if (!target) return;
				e.preventDefault();
				lenis.scrollTo(target, { offset: -80 });
			});
		});
	}

	/* ---------- Scroll-reveals ---------- */
	function initReveals() {
		var items = document.querySelectorAll("[data-reveal]");
		if (!items.length) return;

		// Zonder IntersectionObserver: alles direct tonen.
		if (reduceMotion || !("IntersectionObserver" in window)) {
			items.forEach(function (el) { el.classList.add("is-revealed"); });
			return;
		}

		var io = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (!entry.isIntersecting) return;
					var el = entry.target;
					var delay = parseFloat(el.dataset.reveal) || 0;
					setTimeout(function () { el.classList.add("is-revealed"); }, delay * 1000);
					io.unobserve(el);
				});
			},
			{ rootMargin: "0px 0px -12% 0px", threshold: 0.1 }
		);

		items.forEach(function (el) { io.observe(el); });
	}

	/* ---------- Woord-voor-woord effect ---------- */
	function initWordReveal() {
		var blocks = document.querySelectorAll(".reveal-words");
		if (!blocks.length) return;

		blocks.forEach(function (block) {
			if (block.dataset.split === "done") return;
			var words = block.textContent.trim().split(/\s+/);
			block.textContent = "";
			words.forEach(function (word, i) {
				var span = document.createElement("span");
				span.textContent = word;
				block.appendChild(span);
				if (i < words.length - 1) block.appendChild(document.createTextNode(" "));
			});
			block.dataset.split = "done";
		});

		if (reduceMotion) {
			document.querySelectorAll(".reveal-words span").forEach(function (s) {
				s.classList.add("is-lit");
			});
			return;
		}

		// Met GSAP: koppelen aan scroll. Zonder GSAP: oplichten zodra in beeld.
		if (typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined") {
			gsap.registerPlugin(ScrollTrigger);
			blocks.forEach(function (block) {
				gsap.to(block.querySelectorAll("span"), {
					opacity: 1,
					stagger: 0.05,
					ease: "none",
					scrollTrigger: {
						trigger: block,
						start: "top 82%",
						end: "bottom 62%",
						scrub: true
					}
				});
			});
		} else if ("IntersectionObserver" in window) {
			var io = new IntersectionObserver(function (entries) {
				entries.forEach(function (entry) {
					if (!entry.isIntersecting) return;
					var spans = entry.target.querySelectorAll("span");
					spans.forEach(function (s, i) {
						setTimeout(function () { s.classList.add("is-lit"); }, i * 45);
					});
					io.unobserve(entry.target);
				});
			}, { threshold: 0.3 });
			blocks.forEach(function (b) { io.observe(b); });
		}
	}

	/* ---------- Navigatie ---------- */
	function initNav() {
		var nav = document.querySelector(".nav");
		if (!nav) return;

		var toggle = nav.querySelector(".nav__toggle");
		if (toggle) {
			toggle.addEventListener("click", function () {
				var open = nav.classList.toggle("is-open");
				toggle.setAttribute("aria-expanded", open ? "true" : "false");
				toggle.textContent = open ? "Sluiten" : "Menu";
			});
			nav.querySelectorAll(".nav__links a").forEach(function (a) {
				a.addEventListener("click", function () {
					nav.classList.remove("is-open");
					toggle.setAttribute("aria-expanded", "false");
					toggle.textContent = "Menu";
				});
			});
		}

		var onScroll = function () {
			nav.classList.toggle("is-stuck", window.scrollY > 8);
		};
		onScroll();
		window.addEventListener("scroll", onScroll, { passive: true });
	}

	/* ---------- Cookietoestemming ----------
	   Analytics wordt pas geladen ná toestemming. Zolang er geen
	   meet-ID is ingevuld gebeurt er niets — zie loadAnalytics().
	------------------------------------------------------------- */
	var CONSENT_KEY = "8eon.consent";

	function loadAnalytics() {
		var id = document.documentElement.dataset.analyticsId;
		if (!id || id.indexOf("VUL_IN") === 0) return; // nog niet geconfigureerd
		if (document.getElementById("ga-src")) return;

		var s = document.createElement("script");
		s.id = "ga-src";
		s.async = true;
		s.src = "https://www.googletagmanager.com/gtag/js?id=" + id;
		document.head.appendChild(s);

		window.dataLayer = window.dataLayer || [];
		window.gtag = function () { window.dataLayer.push(arguments); };
		window.gtag("js", new Date());
		window.gtag("config", id, { anonymize_ip: true });
	}

	function initCookies() {
		var banner = document.querySelector(".cookie");
		var choice = null;
		try { choice = localStorage.getItem(CONSENT_KEY); } catch (e) { /* private mode */ }

		if (choice === "accepted") {
			loadAnalytics();
			return;
		}
		if (choice === "declined" || !banner) return;

		banner.hidden = false;

		function decide(value) {
			try { localStorage.setItem(CONSENT_KEY, value); } catch (e) { /* negeren */ }
			banner.hidden = true;
			if (value === "accepted") loadAnalytics();
		}

		var accept = banner.querySelector("[data-consent='accept']");
		var decline = banner.querySelector("[data-consent='decline']");
		if (accept) accept.addEventListener("click", function () { decide("accepted"); });
		if (decline) decline.addEventListener("click", function () { decide("declined"); });
	}

	/* ---------- Meetpunten ---------- */
	function initTracking() {
		// Klik op een live demo = koopklaar-signaal.
		document.querySelectorAll("[data-track-demo]").forEach(function (el) {
			el.addEventListener("click", function () {
				if (typeof window.gtag !== "function") return;
				window.gtag("event", "demo_geopend", {
					dashboard: el.dataset.trackDemo
				});
			});
		});

		document.querySelectorAll("[data-track-cta]").forEach(function (el) {
			el.addEventListener("click", function () {
				if (typeof window.gtag !== "function") return;
				window.gtag("event", "cta_geklikt", { plek: el.dataset.trackCta });
			});
		});
	}

	/* ---------- Start ---------- */
	function boot() {
		initNav();
		initLenis();
		initWordReveal();
		initReveals();
		initCookies();
		initTracking();

		var year = document.querySelector("[data-year]");
		if (year) year.textContent = new Date().getFullYear();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();
