import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

const PRESENTATION_STORAGE_KEY = "repairflow.presentation-mode";
const PresentationModeContext = createContext(false);

function requestedByUrl(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("presentation") === "1";
}

function storedMode(): boolean {
  return (
    typeof sessionStorage !== "undefined" &&
    sessionStorage.getItem(PRESENTATION_STORAGE_KEY) === "1"
  );
}

/** An explicit per-tab rehearsal view. `?presentation=1` enables it and the
 * choice persists across client navigation for this browser session. */
export function PresentationModeProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const requested = requestedByUrl();
    const next = requested || storedMode();
    if (requested) sessionStorage.setItem(PRESENTATION_STORAGE_KEY, "1");
    setEnabled(next);
  }, []);

  return (
    <PresentationModeContext.Provider value={enabled}>{children}</PresentationModeContext.Provider>
  );
}

export function usePresentationMode(): boolean {
  return useContext(PresentationModeContext);
}
