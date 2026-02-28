import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { ToastProvider } from './hooks/useToast';
import Layout from './components/Layout';
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

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<HomePage />} />

              {/* Auth */}
              <Route path="/auth/login" element={<LoginPage />} />
              <Route path="/auth/signup" element={<SignupPage />} />
              <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
              <Route path="/auth/logout" element={<LogoutPage />} />

              {/* Kit CRUD */}
              <Route path="/kit/new" element={<KitCreatePage />} />
              <Route path="/kit/:slug" element={<KitDetailPage />} />

              {/* Kit Execution */}
              <Route path="/kit/:slug/run" element={<KitRunPage />} />
              <Route path="/kit/:slug/history" element={<KitHistoryPage />} />
              <Route path="/kit/:slug/history/:runId" element={<ExecutionDetailPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
