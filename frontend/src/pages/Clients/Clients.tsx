import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { clientsApi } from '../../api/clients';
import type { Client } from '../../types';
import styles from './Clients.module.css';

interface ClientForm {
  name: string;
  telegram_id: string;
  phone: string;
}

export default function Clients() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ClientForm>();

  const fetchClients = async () => {
    try {
      const res = await clientsApi.getAll();
      setClients(res.data);
    } catch {
      toast.error('Ошибка загрузки клиентов');
    }
  };

  useEffect(() => { fetchClients(); }, []);

  const onSubmit = async (data: ClientForm) => {
    setLoading(true);
    try {
      await clientsApi.create({
        name: data.name || undefined,
        telegram_id: parseInt(data.telegram_id),
        phone: data.phone || undefined,
      });
      toast.success('Клиент создан');
      setShowForm(false);
      reset();
      fetchClients();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка создания');
    } finally {
      setLoading(false);
    }
  };

  const toggleBlock = async (client: Client) => {
    try {
      await clientsApi.update(client.id, { is_blocked: !client.is_blocked });
      toast.success(client.is_blocked ? 'Клиент разблокирован' : 'Клиент заблокирован');
      fetchClients();
    } catch {
      toast.error('Ошибка обновления статуса');
    }
  };

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>Клиенты</h1>
        <button className={styles.primaryBtn} onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Отмена' : '+ Добавить клиента'}
        </button>
      </div>

      {showForm && (
        <div className={styles.card}>
            <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
            <div className={styles.inputGroup}>
                <label className={styles.label}>Имя</label>
                <input className={styles.input} {...register('name')} placeholder="Иван Иванов" />
            </div>
            <div className={styles.inputGroup}>
                <label className={styles.label}>Telegram ID *</label>
                <input className={styles.input} type="number" {...register('telegram_id', { required: true })} />
                {errors.telegram_id && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>
            <div className={styles.inputGroup}>
                <label className={styles.label}>Телефон</label>
                <input className={styles.input} {...register('phone')} placeholder="+375..." />
            </div>
            <div className={styles.formActions}>
                <button type="submit" className={styles.primaryBtn} disabled={loading}>
                {loading ? 'Создание...' : 'Создать'}
                </button>
            </div>
            </form>
        </div>
    )}

      <div className={styles.card}>
        {clients.length === 0 ? (
          <div className={styles.emptyState}>Нет клиентов</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Telegram ID</th>
                <th>Телефон</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>{c.name || '-'}</td>
                  <td>{c.telegram_id}</td>
                  <td>{c.phone || '-'}</td>
                  <td>
                    {c.is_blocked
                      ? <span className={styles.blockedBadge}>Заблокирован</span>
                      : <span className={styles.activeBadge}>Активен</span>}
                  </td>
                  <td>
                    <button className={styles.dangerBtn} onClick={() => toggleBlock(c)}>
                      {c.is_blocked ? 'Разблокировать' : 'Заблокировать'}
                    </button>
                  </ td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}