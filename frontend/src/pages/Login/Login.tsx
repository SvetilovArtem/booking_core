import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import api from '../../api';
import { useAuthStore } from '../../store/auth';
import styles from './Login.module.css';

interface LoginForm {
  name: string;
  password: string;
}

export default function Login() {
  const navigate = useNavigate();
  const { setToken } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    setLoading(true);
    try {
        const response = await api.post('/admins/login', data);
        setToken(response.data.access_token, response.data.expires_in);
      toast.success('Вход выполнен');
      navigate('/');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>Booking Core</h1>
        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Логин</label>
            <input
              className={styles.input}
              {...register('name', { required: 'Введите логин' })}
              placeholder="admin"
            />
            {errors.name && <span style={{color: 'var(--danger)', fontSize: '12px'}}>{errors.name.message}</span>}
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Пароль</label>
            <input
              type="password"
              className={styles.input}
              {...register('password', { required: 'Введите пароль' })}
              placeholder="••••••••"
            />
            {errors.password && <span style={{color: 'var(--danger)', fontSize: '12px'}}>{errors.password.message}</span>}
          </div>
          <button type="submit" className={styles.button} disabled={loading}>
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  );
}