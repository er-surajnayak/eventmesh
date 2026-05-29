import React, { useMemo } from 'react';

export function StaticMesh({ scattered = false, accent = '#00D6FF', width = 320, height = 220 }) {
  const nodes = useMemo(() => {
    const rng = (seed => () => (seed = (seed * 9301 + 49297) % 233280) / 233280)(42);
    const clusters = scattered
      ? [
          { cx: 0.2, cy: 0.25, r: 0.12 },
          { cx: 0.78, cy: 0.22, r: 0.1 },
          { cx: 0.22, cy: 0.78, r: 0.1 },
          { cx: 0.78, cy: 0.78, r: 0.12 },
        ]
      : [{ cx: 0.5, cy: 0.5, r: 0.42 }];
    const all = [];
    clusters.forEach((c, ci) => {
      const count = scattered ? 6 : 22;
      for (let i = 0; i < count; i++) {
        const a = rng() * Math.PI * 2;
        const rr = Math.sqrt(rng()) * c.r;
        all.push({
          x: (c.cx + Math.cos(a) * rr) * width,
          y: (c.cy + Math.sin(a) * rr) * height,
          cluster: ci,
          hub: i === 0,
        });
      }
    });
    return all;
  }, [scattered, width, height]);

  const edges = useMemo(() => {
    const out = [];
    const maxD = scattered ? 50 : 70;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (scattered && nodes[i].cluster !== nodes[j].cluster) continue;
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const d = Math.sqrt(dx*dx + dy*dy);
        if (d < maxD) out.push({ a: i, b: j, d });
      }
    }
    return out;
  }, [nodes, scattered]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%" style={{ display: 'block' }}>
      <defs>
        <radialGradient id={`glow-${scattered ? 's' : 'u'}`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={accent} stopOpacity="0.18" />
          <stop offset="100%" stopColor={accent} stopOpacity="0" />
        </radialGradient>
      </defs>
      {!scattered && <rect x="0" y="0" width={width} height={height} fill={`url(#glow-u)`} />}
      {edges.map((e, i) => {
        const a = nodes[e.a], b = nodes[e.b];
        const op = scattered ? 0.18 : 0.35 * (1 - e.d / 80);
        return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={accent} strokeWidth="0.8" opacity={op} />;
      })}
      {nodes.map((n, i) => (
        <circle key={i} cx={n.x} cy={n.y} r={n.hub ? 3.2 : 1.6} fill={n.hub ? accent : 'rgba(255,255,255,0.7)'} />
      ))}
    </svg>
  );
}
