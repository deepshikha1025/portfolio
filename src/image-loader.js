document.addEventListener("DOMContentLoaded", function() {
  function markLoaded(img) { setTimeout(function() { img.classList.add("loaded"); }, 5000); }
  new MutationObserver(function(muts) {
    muts.forEach(function(m) {
      m.addedNodes.forEach(function(n) {
        if (n.tagName === "IMG") { if (n.complete) markLoaded(n); else n.addEventListener("load", function() { markLoaded(n); }); }
        if (n.querySelectorAll) n.querySelectorAll("img").forEach(function(img) { if (img.complete) markLoaded(img); else img.addEventListener("load", function() { markLoaded(img); }); });
      });
    });
  }).observe(document.body, { childList: true, subtree: true });
  document.querySelectorAll("img").forEach(function(img) { if (img.complete) markLoaded(img); else img.addEventListener("load", function() { markLoaded(img); }); });
});
