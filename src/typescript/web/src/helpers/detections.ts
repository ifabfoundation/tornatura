export function getRangePointColor(v: number): string {
  let c = "#43C318";
  if (v > 0.25) c = "#FFB291";
  if (v > 0.5) c = "#FF4D4E";
  if (v > 0.75) c = "#A10406";
  return c;
}

export function getCounterPointSize(v: number): number {
  return 25;
}
