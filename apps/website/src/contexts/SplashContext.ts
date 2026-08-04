import { createContext } from "react";

export interface SplashContextType {
  isSplashActive: boolean;
  setSplashActive: (active: boolean) => void;
}

export const SplashContext = createContext<SplashContextType>({
  isSplashActive: false,
  setSplashActive: () => {},
});
