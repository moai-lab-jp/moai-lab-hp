// MOAI Lab サイト共通スクリプト：ヘッダー、モバイルメニュー、スクロール時のフェードイン
(function () {
  var root = document.documentElement;
  var head = document.querySelector('.site-head');
  var toggle = document.querySelector('.nav-toggle');
  var mobile = window.matchMedia('(max-width: 1080px)');

  // スクロールでヘッダーを詰める
  function onScroll() {
    if (head) head.classList.toggle('scrolled', window.scrollY > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // モバイルメニューの開閉
  function setMenu(open) {
    root.classList.toggle('nav-open', open);
    if (toggle) toggle.setAttribute('aria-expanded', String(open));
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      setMenu(!root.classList.contains('nav-open'));
    });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      setMenu(false);
      closeDrops(null);
    }
  });

  // ドロップダウン：PCはホバーとフォーカスで開く。クリックとタッチでも開閉できるようにする
  var items = document.querySelectorAll('.nav-item');
  function closeDrops(except) {
    items.forEach(function (item) {
      if (item !== except) {
        item.classList.remove('open');
        item.querySelector('button').setAttribute('aria-expanded', 'false');
      }
    });
  }
  items.forEach(function (item) {
    var button = item.querySelector('button');
    button.addEventListener('click', function () {
      var open = !item.classList.contains('open');
      if (!mobile.matches) closeDrops(item);
      item.classList.toggle('open', open);
      button.setAttribute('aria-expanded', String(open));
    });
  });
  document.addEventListener('click', function (e) {
    if (!mobile.matches && !e.target.closest('.nav-item')) closeDrops(null);
    if (root.classList.contains('nav-open') && !e.target.closest('.site-head')) setMenu(false);
  });
  // モバイルでは、今いるセクションのメニューを最初から開いておく
  if (mobile.matches) {
    var current = document.querySelector('.nav-item.current');
    if (current) {
      current.classList.add('open');
      current.querySelector('button').setAttribute('aria-expanded', 'true');
    }
  }

  // スクロールして見えたらフェードイン
  var targets = document.querySelectorAll('.fade-in');
  if (!('IntersectionObserver' in window)) {
    targets.forEach(function (el) { el.classList.add('visible'); });
    return;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
  targets.forEach(function (el) { observer.observe(el); });
})();
