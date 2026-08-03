import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Login from './pages/Login/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import { useAuthStore } from './store/auth';
import Admins from './pages/Admins/Admins';
import type { JSX } from 'react/jsx-runtime';
import Clients from './pages/Clients/Clients';
import Masters from './pages/Masters/Masters';
import Services from './pages/Services/Services';
import Businesses from './pages/Business/Business';
import Slots from './pages/Slots/Slots';

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
            <Route path="clients" element={<Clients />} />
            <Route path="masters" element={<Masters />} />
            <Route path="services" element={<Services />} />
            <Route path="slots" element={<Slots />} />
            <Route path="orders" element={<div>Записи (в разработке)</div>} />
            <Route path="reports" element={<div>Отчёты (в разработке)</div>} />
            <Route path="admins" element={<Admins />} />
            <Route path="businesses" element={<Businesses />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;