import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Analytics } from "@vercel/analytics/react";
import { AuthProvider } from "./hooks/useAuth";
import { ToastProvider } from "./hooks/useToast";
import Layout from "./components/Layout";
import AuthGuard from "./components/AuthGuard";
import LandingPage from "./pages/LandingPage";
import EarlyAccessPage from "./pages/EarlyAccessPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import LogoutPage from "./pages/LogoutPage";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route element={<Layout />}>
              {/* Public landing page */}
              <Route path="/" element={<LandingPage />} />

              {/* Auth */}
              <Route path="/auth/login" element={<LoginPage />} />
              <Route path="/auth/signup" element={<SignupPage />} />
              <Route
                path="/auth/reset-password"
                element={<ResetPasswordPage />}
              />
              <Route path="/auth/logout" element={<LogoutPage />} />

              {/* Early Access page - requires auth */}
              <Route
                path="/app"
                element={
                  <AuthGuard>
                    <EarlyAccessPage />
                  </AuthGuard>
                }
              />
            </Route>
          </Routes>
        </AuthProvider>
      </ToastProvider>
      <Analytics />
    </BrowserRouter>
  );
}
