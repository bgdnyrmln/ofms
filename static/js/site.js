/* Progressive enhancement only. Everything degrades to a working page without it. */
(function () {
  "use strict";

  console.log("bgdnyrmln.com");

  /* --- menu drawer (phones) --------------------------------------------- */
  var burger = document.querySelector(".top__burger");
  var drawer = document.getElementById("menu");
  if (burger && drawer) {
    var setOpen = function (open) {
      document.body.classList.toggle("nav-open", open);
      burger.setAttribute("aria-expanded", String(open));
      if (open) {
        drawer.removeAttribute("inert");
        var first = drawer.querySelector(".drawer__close");
        if (first) first.focus();
      } else {
        drawer.setAttribute("inert", "");
        burger.focus();
      }
    };
    drawer.setAttribute("inert", "");
    burger.addEventListener("click", function () {
      setOpen(!document.body.classList.contains("nav-open"));
    });
    drawer.addEventListener("click", function (e) {
      if (e.target.closest(".drawer__close, .drawer__nav a")) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && document.body.classList.contains("nav-open")) setOpen(false);
    });
    // a resize into the desktop layout hides the drawer, so drop the scroll lock
    window.addEventListener("resize", function () {
      if (window.innerWidth > 720 && document.body.classList.contains("nav-open")) setOpen(false);
    });
  }

  /* --- ticker: seamless loop on any screen width ------------------------
     Two identical sets slide by exactly one set width. Each set is filled
     with copies of the phrases until it is wider than the screen, so the
     end of one set never shows before the next begins. */
  var track = document.querySelector(".ticker__track");
  if (track) {
    var sets = track.querySelectorAll(".ticker__set");
    var phrases = Array.prototype.slice.call(sets[0].children).map(function (n) { return n.cloneNode(true); });
    var fillTicker = function () {
      var first = sets[0];
      first.innerHTML = "";
      do {
        phrases.forEach(function (n) { first.appendChild(n.cloneNode(true)); });
      } while (first.scrollWidth < window.innerWidth + 50 && first.children.length < 200);
      for (var i = 1; i < sets.length; i++) sets[i].innerHTML = first.innerHTML;
      track.style.animationDuration = Math.max(first.scrollWidth / 45, 8) + "s"; // ~45px per second
    };
    fillTicker();
    var tickerW = window.innerWidth;
    window.addEventListener("resize", function () {
      if (window.innerWidth > tickerW) fillTicker(); // only ever needs more copies
      tickerW = Math.max(tickerW, window.innerWidth);
    });
    if (document.fonts) document.fonts.ready.then(fillTicker);
  }

  /* --- home: header turns solid once the page is scrolled -------------- */
  var top = document.querySelector(".is-home .top");
  if (top) {
    var onScroll = function () { top.classList.toggle("is-solid", window.scrollY > 8); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* --- product page: price + CTA bar while the form is out of sight ----- */
  var bar = document.querySelector(".buybar");
  var order = document.getElementById("buy");
  if (bar && order && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) bar.removeAttribute("data-visible");
        else bar.setAttribute("data-visible", "");
      });
    }).observe(order);
  } else if (bar) {
    bar.setAttribute("data-visible", "");
  }

  /* --- gallery slide counter ------------------------------------------- */
  var gallery = document.querySelector("[data-gallery]");
  var count = document.querySelector("[data-count]");
  if (gallery && count) {
    var slides = gallery.querySelectorAll(".product__slide");
    var update = function () {
      var i = Math.round(gallery.scrollLeft / gallery.clientWidth) + 1;
      count.firstElementChild.textContent = Math.min(Math.max(i, 1), slides.length);
    };
    gallery.addEventListener("scroll", function () {
      window.clearTimeout(gallery._t);
      gallery._t = window.setTimeout(update, 60);
    }, { passive: true });
  }
})();
