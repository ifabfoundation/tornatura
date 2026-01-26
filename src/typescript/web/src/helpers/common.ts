import { useState, useEffect } from "react";

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
