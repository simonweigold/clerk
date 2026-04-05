import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
import DocsPage from "./pages/DocsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
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

                {/* Early Access page - requires auth, no backend access */}
                <Route
                  path="/app"
                  element={
                    <AuthGuard>
                      <EarlyAccessPage />
                    </AuthGuard>
                  }
                />

                {/* App routes disabled for launch - redirect to early access */}
                <Route path="/home" element={<Navigate to="/app" replace />} />
                <Route path="/kit/new" element={<Navigate to="/app" replace />} />
                <Route path="/kit/:slug" element={<Navigate to="/app" replace />} />
                <Route path="/kit/:slug/run" element={<Navigate to="/app" replace />} />
                <Route path="/kit/:slug/history" element={<Navigate to="/app" replace />} />
                <Route path="/kit/:slug/history/:runId" element={<Navigate to="/app" replace />} />
                <Route path="/settings" element={<Navigate to="/app" replace />} />

                {/* Docs */}
                <Route path="/docs/*" element={<DocsPage />} />
              </Route>
            </Routes>
          </AuthProvider>
        </ToastProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
