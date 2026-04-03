import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './hooks/useAuth';
import { ToastProvider } from './hooks/useToast';
import Layout from './components/Layout';
import AuthGuard from './components/AuthGuard';
import LandingPage from './pages/LandingPage';
import EarlyAccessPage from './pages/EarlyAccessPage';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import LogoutPage from './pages/LogoutPage';
import KitDetailPage from './pages/KitDetailPage';
import KitCreatePage from './pages/KitCreatePage';
import KitRunPage from './pages/KitRunPage';
import KitHistoryPage from './pages/KitHistoryPage';
import ExecutionDetailPage from './pages/ExecutionDetailPage';
import SettingsPage from './pages/SettingsPage';
import DocsPage from './pages/DocsPage';

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
                <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
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

                {/* App routes - hidden/unlinked for launch */}
                <Route path="/home" element={<HomePage />} />
                <Route path="/kit/new" element={<KitCreatePage />} />
                <Route path="/kit/:slug" element={<KitDetailPage />} />
                <Route path="/kit/:slug/run" element={<KitRunPage />} />
                <Route path="/kit/:slug/history" element={<KitHistoryPage />} />
                <Route path="/kit/:slug/history/:runId" element={<ExecutionDetailPage />} />
                <Route path="/settings" element={<SettingsPage />} />

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
