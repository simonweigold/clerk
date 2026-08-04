import { useContext } from "react";
import { SplashContext } from "../contexts/SplashContext";
import type { SplashContextType } from "../contexts/SplashContext";

export function useSplash(): SplashContextType {
  return useContext(SplashContext);
}
