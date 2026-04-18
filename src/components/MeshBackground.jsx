import React, { useRef, useMemo, useEffect } from 'react';

export function MeshBackground({ intensity = 0.8, accent = '#00D6FF', interactive = true, density = 1 }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const mouseRef = useRef({ x: -1e4, y: -1e4, active: false });
  const stateRef = useRef({ nodes: [], w: 0, h: 0, dpr: 1 });

  const accentRgb = useMemo(() => {
    const m = accent.replace('#','');
    const n = parseInt(m, 16);
    return { r: (n>>16)&255, g: (n>>8)&255, b: n&255 };
  }, [accent]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    const st = stateRef.current;

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const parent = canvas.parentElement;
      if (!parent) return;
      const rect = parent.getBoundingClientRect();
      st.w = rect.width;
      st.h = rect.height;
      st.dpr = dpr;
      canvas.width = Math.floor(rect.width * dpr);
      canvas.height = Math.floor(rect.height * dpr);
      canvas.style.width = rect.width + 'px';
      canvas.style.height = rect.height + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seed();
    }

    function seed() {
      const area = st.w * st.h;
      const count = Math.round(Math.min(90, Math.max(28, (area / 18000) * density)));
      const nodes = [];
      for (let i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * st.w,
          y: Math.random() * st.h,
          vx: (Math.random() - 0.5) * 0.18,
          vy: (Math.random() - 0.5) * 0.18,
          r: Math.random() * 1.4 + 0.6,
          pulse: Math.random() * Math.PI * 2,
          hub: Math.random() < 0.12,
        });
      }
      st.nodes = nodes;
    }

    function onMove(e) {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current.x = e.clientX - rect.left;
      mouseRef.current.y = e.clientY - rect.top;
      mouseRef.current.active = true;
    }
    function onLeave() {
      mouseRef.current.active = false;
      mouseRef.current.x = -1e4;
      mouseRef.current.y = -1e4;
    }

    const LINK_DIST = 140;
    const LINK_DIST_SQ = LINK_DIST * LINK_DIST;
    const MOUSE_DIST = 180;

    function tick() {
      const { w, h, nodes } = st;
      ctx.clearRect(0, 0, w, h);

      const grad = ctx.createRadialGradient(w * 0.5, h * 0.45, 0, w * 0.5, h * 0.45, Math.max(w, h) * 0.6);
      grad.addColorStop(0, `rgba(${accentRgb.r},${accentRgb.g},${accentRgb.b},${0.05 * intensity})`);
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < -10) n.x = w + 10;
        if (n.x > w + 10) n.x = -10;
        if (n.y < -10) n.y = h + 10;
        if (n.y > h + 10) n.y = -10;
        n.pulse += 0.012;

        if (mouseRef.current.active && interactive) {
          const dx = n.x - mouseRef.current.x;
          const dy = n.y - mouseRef.current.y;
          const d = Math.sqrt(dx*dx + dy*dy);
          if (d < MOUSE_DIST && d > 0) {
            const force = (1 - d / MOUSE_DIST) * 0.6;
            n.x += (dx / d) * force;
            n.y += (dy / d) * force;
          }
        }
      }

      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx*dx + dy*dy;
          if (d2 < LINK_DIST_SQ) {
            const alpha = (1 - d2 / LINK_DIST_SQ) * 0.28 * intensity;
            ctx.strokeStyle = `rgba(${accentRgb.r},${accentRgb.g},${accentRgb.b},${alpha})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }

        if (mouseRef.current.active && interactive) {
          const dx = a.x - mouseRef.current.x;
          const dy = a.y - mouseRef.current.y;
          const d2 = dx*dx + dy*dy;
          if (d2 < MOUSE_DIST * MOUSE_DIST) {
            const alpha = (1 - Math.sqrt(d2) / MOUSE_DIST) * 0.5 * intensity;
            ctx.strokeStyle = `rgba(${accentRgb.r},${accentRgb.g},${accentRgb.b},${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(mouseRef.current.x, mouseRef.current.y);
            ctx.stroke();
          }
        }
      }

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        const breathe = 0.8 + 0.2 * Math.sin(n.pulse);
        const r = (n.hub ? n.r * 2.2 : n.r) * breathe;
        if (n.hub) {
          const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 6);
          g.addColorStop(0, `rgba(${accentRgb.r},${accentRgb.g},${accentRgb.b},${0.25 * intensity})`);
          g.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.arc(n.x, n.y, r * 6, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.fillStyle = n.hub
          ? `rgba(${accentRgb.r},${accentRgb.g},${accentRgb.b},${0.95 * intensity})`
          : `rgba(255,255,255,${(n.hub ? 0.9 : 0.55) * intensity})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(tick);
    }

    resize();
    rafRef.current = requestAnimationFrame(tick);
    const ro = new ResizeObserver(resize);
    ro.observe(canvas.parentElement);
    if (interactive) {
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseleave', onLeave);
    }
    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseleave', onLeave);
    };
  }, [intensity, accentRgb.r, accentRgb.g, accentRgb.b, interactive, density]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
      }}
    />
  );
}
