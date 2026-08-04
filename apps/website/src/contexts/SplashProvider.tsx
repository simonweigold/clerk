import { useState, type ReactNode } from "react";
import { SplashContext } from "./SplashContext";

export function SplashProvider({ children }: { children: ReactNode }) {
  const [isSplashActive, setSplashActive] = useState(false);
  return (
    <SplashContext.Provider value={{ isSplashActive, setSplashActive }}>
      {children}
    </SplashContext.Provider>
  );
}
