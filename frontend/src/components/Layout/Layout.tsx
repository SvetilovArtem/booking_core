import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';
import { useThemeStore } from '../../store/theme';
import toast from 'react-hot-toast';
import styles from './Layout.module.css';

const navItems = [
  { path: '/', label: 'Дашборд', icon: '📊' },
  { path: '/clients', label: 'Клиенты', icon: '👥' },
  { path: '/masters', label: 'Мастера', icon: '👨‍' },
  { path: '/services', label: 'Услуги', icon: '💇' },
  { path: '/slots', label: 'Слоты', icon: '🕐' },
  { path: '/orders', label: 'Записи', icon: '📅' },
  { path: '/reports', label: 'Отчёты', icon: '📈' },
  { path: '/admins', label: 'Админы', icon: '🛡️' },
];

export default function Layout() {
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();

  const handleLogout = () => {
    logout();
    toast.success('Выход выполнен');
    navigate('/login');
  };

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>Booking Core</div>
        <nav className={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className={styles.footer}>
          <button onClick={toggleTheme} className={styles.footerBtn}>
            <span>{theme === 'light' ? '' : '☀️'}</span>
            {theme === 'light' ? 'Тёмная тема' : 'Светлая тема'}
          </button>
          <button onClick={handleLogout} className={styles.footerBtn}>
            <span></span>
            Выйти
          </button>
        </div>
      </aside>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}