import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Spinner } from '@chakra-ui/react';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminRoute } from './components/AdminRoute';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';

const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const AuthCallbackPage = lazy(() => import('./pages/AuthCallbackPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const NewSubmissionPage = lazy(() => import('./pages/NewSubmissionPage'));
const SubmissionsPage = lazy(() => import('./pages/SubmissionsPage'));
const SubmissionDetailPage = lazy(() => import('./pages/SubmissionDetailPage'));
const RoastPage = lazy(() => import('./pages/RoastPage'));
const RoastHistoryPage = lazy(() => import('./pages/RoastHistoryPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const AdminUsersPage = lazy(() => import('./pages/AdminUsersPage'));
const AdminSubmissionsPage = lazy(() => import('./pages/AdminSubmissionsPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <Suspense fallback={<Spinner m={8} />}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route element={<AppLayout />}>
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
          <Route path="/submissions/new" element={<ProtectedRoute><NewSubmissionPage /></ProtectedRoute>} />
          <Route path="/submissions" element={<ProtectedRoute><SubmissionsPage /></ProtectedRoute>} />
          <Route path="/submissions/:id" element={<ProtectedRoute><SubmissionDetailPage /></ProtectedRoute>} />
          <Route path="/roasts" element={<ProtectedRoute><RoastHistoryPage /></ProtectedRoute>} />
          <Route path="/roasts/:submissionId" element={<ProtectedRoute><RoastPage /></ProtectedRoute>} />
          <Route path="/admin" element={<AdminRoute><AdminDashboardPage /></AdminRoute>} />
          <Route path="/admin/users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
          <Route path="/admin/submissions" element={<AdminRoute><AdminSubmissionsPage /></AdminRoute>} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
