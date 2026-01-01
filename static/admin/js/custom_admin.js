(function(){
  function qs(s,r){return (r||document).querySelector(s);}
  function qsa(s,r){return Array.from((r||document).querySelectorAll(s));}

  const root = qs("[data-x-accordion]");
  if(!root) return;

  // Toggle sections
  root.addEventListener("click", function(e){
    const btn = e.target.closest("[data-x-toggle]");
    if(!btn) return;
    const item = btn.closest("[data-x-item]");
    item.classList.toggle("is-open");
  });

  // Collapse all
  const collapse = qs("[data-action='collapse-all']");
  if(collapse){
    collapse.addEventListener("click", function(){
      qsa("[data-x-item]", root).forEach(i=>i.classList.remove("is-open"));
    });
  }

  // Open active model automatically
  const current = location.pathname;
  qsa(".x-acc-link a", root).forEach(a=>{
    if(a.getAttribute("href") === current){
      a.classList.add("is-active");
      a.closest("[data-x-item]").classList.add("is-open");
    }
  });
})();
