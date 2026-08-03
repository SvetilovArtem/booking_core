import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import api from '../../api';
import type { Admin } from '../../types';
import styles from './Admins.module.css';

interface AdminForm {
  name: string;
  password: string;
  phone?: string;
  telegram_id?: string;
}

export default function Admins() {
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<AdminForm>();

  const fetchAdmins = async () => {
    try {
      const response = await api.get('/admins/');
      setAdmins(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки админов');
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  const onSubmit = async (data: AdminForm) => {
    setLoading(true);
    try {
      const payload = {
        ...data,
        telegram_id: data.telegram_id ? parseInt(data.telegram_id) : null,
      };
      await api.post('/admins/register', payload);
      toast.success('Админ успешно создан');
      setShowForm(false);
      reset();
      fetchAdmins();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ошибка создания');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)' }}>Администраторы</h1>
        <button
          className={styles.primaryBtn}
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Отмена' : '+ Добавить админа'}
        </button>
      </div>

      {showForm && (
        <div className={styles.card}>
          <h3 style={{ marginBottom: '16px', color: 'var(--text-primary)' }}>Новый администратор</h3>
          <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Логин *</label>
              <input className={styles.input} {...register('name', { required: true })} />
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Пароль *</label>
              <input type="password" className={styles.input} {...register('password', { required: true })} />
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Телефон</label>
              <input className={styles.input} {...register('phone')} />
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Telegram ID</label>
              <input type="number" className={styles.input} {...register('telegram_id')} />
            </div>
            <button type="submit" className={styles.primaryBtn} disabled={loading} style={{ marginTop: '16px' }}>
              {loading ? 'Создание...' : 'Создать'}
            </button>
          </form>
        </div>
      )}

      <div className={styles.card}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Логин</th>
              <th>Телефон</th>
              <th>Telegram ID</th>
              <th>Дата создания</th>
            </tr>
          </thead>
          <tbody>
            {admins.map((admin) => (
              <tr key={admin.id}>
                <td>{admin.id}</td>
                <td style={{ fontWeight: 500 }}>{admin.name}</td>
                <td>{admin.phone || '-'}</td>
                <td>{admin.telegram_id || '-'}</td>
                <td>{new Date(admin.created_at).toLocaleDateString('ru-RU')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}