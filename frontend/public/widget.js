(function () {
  "use strict";
  var script = document.currentScript || (function () {
    var scripts = document.getElementsByTagName("script");
    return scripts[scripts.length - 1];
  })();
  var orgSlug = script.getAttribute("data-org");
  if (!orgSlug) { console.warn("[AI Sales Widget] Missing data-org attribute."); return; }
  var baseUrl = script.src.replace("/widget.js", "");

  var style = document.createElement("style");
  style.textContent = [
    "#aise-btn{position:fixed;bottom:24px;right:24px;z-index:9998;width:56px;height:56px;border-radius:50%;",
    "background:#6366f1;color:#fff;border:none;cursor:pointer;box-shadow:0 4px 16px rgba(99,102,241,.4);",
    "display:flex;align-items:center;justify-content:center;transition:transform .2s,box-shadow .2s;font-size:22px;}",
    "#aise-btn:hover{transform:scale(1.1);box-shadow:0 6px 20px rgba(99,102,241,.5);}",
    "#aise-wrap{position:fixed;bottom:90px;right:24px;z-index:9999;width:420px;max-width:calc(100vw - 32px);",
    "height:620px;max-height:calc(100vh - 110px);border-radius:16px;overflow:hidden;",
    "box-shadow:0 8px 40px rgba(0,0,0,.18);display:none;}",
    "#aise-wrap.open{display:block;}",
    "#aise-iframe{width:100%;height:100%;border:none;}",
  ].join("");
  document.head.appendChild(style);

  var btn = document.createElement("button");
  btn.id = "aise-btn";
  btn.setAttribute("aria-label", "Open contact form");
  btn.innerHTML = "💬";
  document.body.appendChild(btn);

  var wrap = document.createElement("div");
  wrap.id = "aise-wrap";
  var iframe = document.createElement("iframe");
  iframe.id = "aise-iframe";
  iframe.setAttribute("allow", "clipboard-write");
  wrap.appendChild(iframe);
  document.body.appendChild(wrap);

  var open = false;
  btn.addEventListener("click", function () {
    open = !open;
    if (open) {
      iframe.src = baseUrl + "/form/" + orgSlug + "?widget=1";
      wrap.classList.add("open");
      btn.innerHTML = "✕";
      btn.setAttribute("aria-label", "Close contact form");
    } else {
      wrap.classList.remove("open");
      btn.innerHTML = "💬";
      btn.setAttribute("aria-label", "Open contact form");
    }
  });
  document.addEventListener("click", function (e) {
    if (open && !wrap.contains(e.target) && e.target !== btn) {
      wrap.classList.remove("open");
      btn.innerHTML = "💬";
      open = false;
    }
  });
})();
