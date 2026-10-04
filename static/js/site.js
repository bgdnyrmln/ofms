/* Mobile behaviour only. Everything degrades to a working page without it. */
(function () {
  "use strict";

  /* --- menu drawer ------------------------------------------------------ */
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

  /* --- wordmark never clips, whatever the brand name is ----------------- */
  var mark = document.querySelector(".hero__mark");
  if (mark) {
    /* Unbounded is wide: a long brand name would clip against nowrap.
       Shrink to fit, iterating because letter-spacing and the webfont swap
       make the first proportional guess only approximate. */
    var fitMark = function () {
      mark.style.fontSize = "";
      var cs = getComputedStyle(mark);
      var pad = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
      var avail = mark.clientWidth - pad;
      if (!(avail > 0)) return;
      var size = parseFloat(cs.fontSize);
      for (var i = 0; i < 8; i++) {
        var text = mark.scrollWidth - pad;
        if (text <= avail) break;
        size = size * (avail / text) * 0.995;
        mark.style.fontSize = size + "px";
      }
    };
    fitMark();
    window.addEventListener("load", fitMark);
    window.addEventListener("resize", fitMark);
    if (document.fonts) {
      document.fonts.ready.then(fitMark);
      try { document.fonts.load("500 16px Unbounded").then(fitMark, function () {}); } catch (e) {}
    }
  }

  /* --- product page: price + CTA bar while the form is out of sight ----- */
  var bar = document.querySelector(".buybar");
  var order = document.getElementById("order");
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
