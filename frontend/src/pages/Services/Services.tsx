import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { servicesApi } from '../../api/services';
import type { Service } from '../../types';
import styles from './Services.module.css';

interface ServiceForm {
  name: string;
  price: string;
}

export default function Services() {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<ServiceForm>();

  const fetchServices = async () => {
    try {
      const res = await servicesApi.getAll();
      setServices(res.data);
    } catch {
      toast.error('Ошибка загрузки услуг');
    }
  };

  useEffect(() => { fetchServices(); }, []);

  const onSubmit = async (data: ServiceForm) => {
    setLoading(true);
    try {
      const payload = { name: data.name, price: parseInt(data.price) };
      if (editingId) {
        await servicesApi.update(editingId, payload);
        toast.success('Услуга обновлена');
      } else {
        await servicesApi.create(payload);
        toast.success('Услуга создана');
      }
      setShowForm(false);
      setEditingId(null);
      reset();
      fetchServices();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (service: Service) => {
    setValue('name', service.name);
    setValue('price', String(service.price));
    setEditingId(service.id);
    setShowForm(true);
  };

  const cancelForm = () => {
    setShowForm(false);
    setEditingId(null);
    reset();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить эту услугу?')) return;
    try {
      await servicesApi.delete(id);
      toast.success('Услуга удалена');
      fetchServices();
    } catch {
      toast.error('Ошибка удаления');
    }
  };

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>Услуги</h1>
        <button className={styles.primaryBtn} onClick={() => { cancelForm(); setShowForm(true); }}>
          + Добавить услугу
        </button>
      </div>

      {showForm && (
        <div className={styles.card}>
          <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Название *</label>
              <input className={styles.input} {...register('name', { required: true })} placeholder="Стрижка мужская" />
              {errors.name && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Цена (BYN) *</label>
              <input className={styles.input} type="number" min="0" {...register('price', { required: true })} placeholder="25" />
              {errors.price && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" className={styles.primaryBtn} disabled={loading}>
                {loading ? 'Сохранение...' : editingId ? 'Обновить' : 'Создать'}
              </button>
              <button type="button" className={styles.secondaryBtn} onClick={cancelForm}>
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      <div className={styles.card}>
        {services.length === 0 ? (
          <div className={styles.emptyState}>Нет услуг</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Цена</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {services.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.name}</td>
                  <td>{s.price} BYN</td>
                  <td>
                    <div className={styles.actionsCell}>
                      <button className={styles.secondaryBtn} onClick={() => startEdit(s)}>Изменить</button>
                      <button className={styles.dangerBtn} onClick={() => handleDelete(s.id)}>Удалить</button>
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