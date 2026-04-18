import { useEffect } from 'react';

export function useRevealOnScroll() {
  useEffect(() => {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      }
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    const observeAll = () => {
      document.querySelectorAll('.reveal:not(.in)').forEach(el => io.observe(el));
    };
    observeAll();

    const mo = new MutationObserver(() => observeAll());
    mo.observe(document.body, { childList: true, subtree: true });

    const timer = setTimeout(() => {
      document.querySelectorAll('.reveal:not(.in)').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.top < window.innerHeight && r.bottom > 0) el.classList.add('in');
      });
    }, 800);

    return () => { 
      io.disconnect(); 
      mo.disconnect(); 
      clearTimeout(timer); 
    };
  }, []);
}
