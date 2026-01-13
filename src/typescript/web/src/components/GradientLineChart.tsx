import React, { useMemo, useRef } from "react";

type Point = { x: number; y: number; color: string };

type LineChartProps = {
  xMin?: number;
  xMax?: number;
  yMin?: number;
  yMax?: number;
  data: Point[];
  height: number;
  strokeWidth?: number;
  padding?: number | { top?: number; right?: number; bottom?: number; left?: number };
  dotSize?: number; // configurable dot size
};

export function GradientLineChart({
  xMin,
  xMax,
  yMin,
  yMax,
  data,
  height,
  strokeWidth = 2,
  padding = 20,
  dotSize,
}: LineChartProps) {
  const vbWidth = 1000;
  const vbHeight = Math.max(1, height);
  const uid = useRef(Math.random().toString(36).slice(2));

  // Compute ranges dynamically if not provided
  const xs = data.map((d) => d.x);
  const ys = data.map((d) => d.y);
  const minX = xMin ?? Math.min(...xs);
  const maxX = xMax ?? Math.max(...xs);
  const minY = yMin ?? Math.min(...ys);
  const maxY = yMax ?? Math.max(...ys);

  const points = useMemo(() => {
    const innerW =
      vbWidth -
      (typeof padding === "number" ? padding * 2 : (padding.left ?? 0) + (padding.right ?? 0));
    const innerH =
      vbHeight -
      (typeof padding === "number" ? padding * 2 : (padding.top ?? 0) + (padding.bottom ?? 0));
    const xScale = (x: number) =>
      (typeof padding === "number" ? padding : padding.left ?? 0) +
      ((x - minX) / (maxX - minX || 1)) * innerW;
    const yScale = (y: number) =>
      (typeof padding === "number" ? padding : padding.top ?? 0) +
      (1 - (y - minY) / (maxY - minY || 1)) * innerH;
    return data.map((d) => ({ x: xScale(d.x), y: yScale(d.y), color: d.color }));
  }, [data, minX, maxX, minY, maxY, vbWidth, vbHeight, padding]);

  const gradients = useMemo(() => {
    return points.slice(0, -1).map((a, i) => {
      const b = points[i + 1];
      return (
        <linearGradient
          key={`g-${uid.current}-${i}`}
          id={`g-${uid.current}-${i}`}
          gradientUnits="userSpaceOnUse"
          x1={a.x}
          y1={a.y}
          x2={b.x}
          y2={b.y}
        >
          <stop offset="0%" stopColor={a.color} />
          <stop offset="100%" stopColor={b.color} />
        </linearGradient>
      );
    });
  }, [points]);

  const segments = useMemo(() => {
    return points.slice(0, -1).map((a, i) => {
      const b = points[i + 1];
      return (
        <line
          key={`seg-${i}`}
          x1={a.x}
          y1={a.y}
          x2={b.x}
          y2={b.y}
          stroke={`url(#g-${uid.current}-${i})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
        />
      );
    });
  }, [points, strokeWidth]);

  const vertLines = useMemo(() => {
    return points.map((p, i) => (
      <line
        key={`line-${i}`}
        x1={p.x}
        y1={height + 1000}
        x2={p.x}
        y2={-1000}
        stroke={"#ccc"}
        strokeWidth={2}
        strokeLinecap="round"
        fill="none"
      />
    ));
  }, [points, strokeWidth, dotSize]);

  const dots = useMemo(() => {
    const r = (dotSize ?? strokeWidth) / 2; // default to strokeWidth
    return points.map((p, i) => (
      <circle
        key={`dot-${i}`}
        cx={p.x}
        cy={p.y}
        r={r * 2}
        fill={p.color}
        stroke="rgba(0,0,0,0.2)"
      />
    ));
  }, [points, strokeWidth, dotSize]);

  const dotsBlack = useMemo(() => {
    const r = (dotSize ?? strokeWidth) / 2; // default to strokeWidth
    return points.map((p, i) => (
      <circle key={`dotblack-${i}`} cx={p.x} cy={p.y} r={r} fill="black" />
    ));
  }, [points, strokeWidth, dotSize]);

  return (
    <div
      style={{
        width: "100%",
        background: "#e5e5e5",
        borderRadius: 12,
        boxSizing: "border-box",
      }}
    >
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${vbWidth} ${vbHeight}`}
        // overflow={"visible"}
        preserveAspectRatio="xMidYMid meet" // keep circles circular
      >
        <defs>{gradients}</defs>
        {vertLines}
        {segments}
        {dots}
        {dotsBlack}
      </svg>
    </div>
  );
}
