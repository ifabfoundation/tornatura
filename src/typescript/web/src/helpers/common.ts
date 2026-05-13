import { useState, useEffect } from "react";

// -----------------------------------------------------------------------------
/**
 * USAGE
 * var str = "Last edited: " + timeAgo("2026-05-12T18:30:00");
 * --> "Last edited: Just now"
 * --> "Last edited: 2 hours ago"
 * --> "Last edited: 3 days ago"
 *  */

export function timeAgo(date: string): string {
  const now = new Date();
  const diff = (now.getTime() - new Date(date).getTime()) / 1000; // seconds

  const units = [
    { nameSing: "anno", namePlur: "anni", secs: 60 * 60 * 24 * 365 },
    { nameSing: "mese", namePlur: "mesi", secs: 60 * 60 * 24 * 30 },
    { nameSing: "settimana", namePlur: "settimane", secs: 60 * 60 * 24 * 7 },
    { nameSing: "giorno", namePlur: "giorni", secs: 60 * 60 * 24 },
    { nameSing: "ora", namePlur: "ore", secs: 60 * 60 },
    { nameSing: "minuto", namePlur: "minuti", secs: 60 },
    { nameSing: "secondo", namePlur: "secondi", secs: 1 },
  ];

  if (diff < 5) return "un attimo fa";

  for (const u of units) {
    const value = Math.floor(diff / u.secs);
    if (value >= 1) {
      return `${value} ${value > 1 ? u.namePlur : u.nameSing} fa`;
    }
  }
}

// -----------------------------------------------------------------------------
export function useMediaQuery(query: string): boolean {
  const getMatch = (q: string): boolean => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(q).matches;
  };
  const [matches, setMatches] = useState<boolean>(() => getMatch(query));
  useEffect(() => {
    const media = window.matchMedia(query);
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };
    setMatches(media.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [query]);
  return matches;
}

// -----------------------------------------------------------------------------
// Example usage:
// const isMobile = useIsMobile();
// const isMobile = useIsMobile(600);
export function useIsMobile(breakpoint: number = 576): boolean {
  const getMatch = () =>
    typeof window !== "undefined" && window.matchMedia(`(max-width: ${breakpoint}px)`).matches;
  const [isMobile, setIsMobile] = useState<boolean>(getMatch);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const handler = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches);
    };
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [breakpoint]);
  return isMobile;
}

// -----------------------------------------------------------------------------
// Like processing map function
// val: number, fromMin: number, fromMax: number, toMin: number, toMax: number
export function mapValues(
  val: number,
  fromMin: number,
  fromMax: number,
  toMin: number,
  toMax: number,
): number {
  return ((val - fromMin) / (fromMax - fromMin)) * (toMax - toMin) + toMin;
}

// -----------------------------------------------------------------------------
// function testData(
//   aroundLon: number,
//   aroundLat: number,
//   radiusMeters: number,
//   numPoints: number,
// ): mapPoint[] {
//   const points: mapPoint[] = [];
//   for (let i = 0; i < numPoints; i++) {
//     const angle = Math.random() * 2 * Math.PI;
//     const distance = Math.random() * radiusMeters;
//     const dx = distance * Math.cos(angle);
//     const dy = distance * Math.sin(angle);

//     // Approximate conversion from meters to degrees
//     const deltaLng = dx / 111320 / Math.cos(aroundLat * (Math.PI / 180));
//     const deltaLat = dy / 110540;

//     const point = {
//       lng: aroundLon + deltaLng,
//       lat: aroundLat + deltaLat,
//       size: 8,
//       color: getRangePointColor(Math.random()),
//     };

//     points.push(point);
//   }
//   return points;
// }

export function isMobileDevice() {
  return (
    window.matchMedia("(pointer: coarse)").matches && !window.matchMedia("(pointer: fine)").matches
  );
}

export function getBrowsingOrigin() {
  // @ts-ignore
  const isPWA =
    window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  if (isPWA) {
    return "PWA";
  } else {
    return "WEB";
  }
}
