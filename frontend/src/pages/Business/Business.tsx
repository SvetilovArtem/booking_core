import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { businessesApi } from '../../api/business';
import type { Business } from '../../types';
import styles from './Business.module.css';

interface BusinessForm {
  name: string;
  timezone: string;
}

const TIMEZONES = [
  'Europe/Minsk',
  'Europe/Moscow',
  'Europe/Kyiv',
  'Asia/Almaty',
  'Asia/Tashkent',
  'UTC',
];

export default function Businesses() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<BusinessForm>({
    defaultValues: { timezone: 'Europe/Minsk' },
  });

  const fetchBusinesses = async () => {
    try {
      const res = await businessesApi.getAll();
      setBusinesses(res.data);
    } catch {
      toast.error('Ошибка загрузки салонов');
    }
  };

  useEffect(() => { fetchBusinesses(); }, []);

  const onSubmit = async (data: BusinessForm) => {
    setLoading(true);
    try {
      if (editingId) {
        await businessesApi.update(editingId, { name: data.name, timezone: data.timezone });
        toast.success('Салон обновлён');
      } else {
        await businessesApi.create({ name: data.name, timezone: data.timezone });
        toast.success('Салон создан');
      }
      resetForm();
      fetchBusinesses();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (business: Business) => {
    setValue('name', business.name);
    setValue('timezone', business.timezone);
    setEditingId(business.id);
    setShowForm(true);
  };

  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    reset({ timezone: 'Europe/Minsk' });
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить этот салон?')) return;
    try {
      await businessesApi.delete(id);
      toast.success('Салон удалён');
      fetchBusinesses();
    } catch {
      toast.error('Ошибка удаления');
    }
  };

  const toggleActive = async (business: Business) => {
    try {
      await businessesApi.update(business.id, { is_active: !business.is_active });
      toast.success(business.is_active ? 'Салон деактивирован' : 'Салон активирован');
      fetchBusinesses();
    } catch {
      toast.error('Ошибка обновления статуса');
    }
  };

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>Салоны</h1>
        <button className={styles.primaryBtn} onClick={() => { resetForm(); setShowForm(true); }}>
          + Добавить салон
        </button>
      </div>

      {showForm && (
        <div className={styles.card}>
          <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Название *</label>
              <input className={styles.input} {...register('name', { required: true })} placeholder="Барбершоп Центр" />
              {errors.name && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Часовой пояс</label>
              <select className={styles.input} {...register('timezone')}>
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" className={styles.primaryBtn} disabled={loading}>
                {loading ? 'Сохранение...' : editingId ? 'Обновить' : 'Создать'}
              </button>
              <button type="button" className={styles.secondaryBtn} onClick={resetForm}>
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      <div className={styles.card}>
        {businesses.length === 0 ? (
          <div className={styles.emptyState}>Нет салонов</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Часовой пояс</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {businesses.map((b) => (
                <tr key={b.id}>
                  <td>{b.id}</td>
                  <td>{b.name}</td>
                  <td>{b.timezone}</td>
                  <td>
                    {b.is_active
                      ? <span className={styles.activeBadge}>Активен</span>
                      : <span className={styles.inactiveBadge}>Неактивен</span>}
                  </td>
                  <td>
                    <div className={styles.actionsCell}>
                      <button className={styles.secondaryBtn} onClick={() => startEdit(b)}>Изменить</button>
                      <button className={styles.dangerBtn} onClick={() => toggleActive(b)}>
                        {b.is_active ? 'Деакт.' : 'Акт.'}
                      </button>
                      <button className={styles.dangerBtn} onClick={() => handleDelete(b.id)}>Удалить</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}