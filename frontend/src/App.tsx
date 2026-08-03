import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Login from './pages/Login/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import { useAuthStore } from './store/auth';
import Admins from './pages/Admins/Admins';
import type { JSX } from 'react/jsx-runtime';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <>
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="clients" element={<div>Клиенты (в разработке)</div>} />
            <Route path="masters" element={<div>Мастера (в разработке)</div>} />
            <Route path="services" element={<div>Услуги (в разработке)</div>} />
            <Route path="slots" element={<div>Слоты (в разработке)</div>} />
            <Route path="orders" element={<div>Записи (в разработке)</div>} />
            <Route path="reports" element={<div>Отчёты (в разработке)</div>} />
            <Route path="admins" element={<Admins />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;