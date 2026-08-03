import { useEffect, useState, useRef } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { mastersApi, selectorsApi, type MasterPayload } from '../../api/masters';
import type { Master, Service, Business } from '../../types';
import styles from './Masters.module.css';

interface MasterFormData {
  name: string;
  phone: string;
  telegram_id: string;
}

function MultiSelectDropdown<T extends { id: number }>({
  items, selectedIds, onToggle, getLabel, placeholder,
}: {
  items: T[]; selectedIds: number[]; onToggle: (id: number) => void;
  getLabel: (item: T) => string; placeholder: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className={styles.dropdown} ref={ref}>
      <div className={styles.dropdownTrigger} onClick={() => setOpen(!open)}>
        {selectedIds.length > 0
          ? <span>Выбрано: {selectedIds.length}</span>
          : <span className={styles.dropdownPlaceholder}>{placeholder}</span>}
        <span className={styles.dropdownArrow}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div className={styles.dropdownMenu}>
          {items.length === 0 && (
            <div style={{ padding: '8px 12px', color: 'var(--text-muted)', fontSize: 13 }}>
              Нет доступных элементов
            </div>
          )}
          {items.map((item) => (
            <label key={item.id} className={styles.dropdownItem}>
              <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => onToggle(item.id)} />
              {getLabel(item)}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Masters() {
  const [masters, setMasters] = useState<Master[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedServiceIds, setSelectedServiceIds] = useState<number[]>([]);
  const [selectedBusinessIds, setSelectedBusinessIds] = useState<number[]>([]);
  const [filterBusinessId, setFilterBusinessId] = useState<number | ''>('');
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<MasterFormData>();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [mRes, sRes, bRes] = await Promise.all([
          mastersApi.getAll().catch(() => ({ data: [] as Master[] })),
          selectorsApi.getServices().catch(() => ({ data: [] as Service[] })),
          selectorsApi.getBusinesses().catch(() => ({ data: [] as Business[] })),
        ]);
        setMasters(mRes.data);
        setServices(sRes.data);
        setBusinesses(bRes.data);
      } catch { toast.error('Ошибка загрузки данных'); }
    };
    fetchData();
  }, []);

  /** Фильтрация мастеров по выбранному салону */
  const filteredMasters = filterBusinessId === ''
    ? masters
    : masters.filter((m) => (m.business_ids || []).includes(filterBusinessId));

  const toggleService = (id: number) =>
    setSelectedServiceIds((p) => p.includes(id) ? p.filter((s) => s !== id) : [...p, id]);

  const toggleBusiness = (id: number) =>
    setSelectedBusinessIds((p) => p.includes(id) ? p.filter((b) => b !== id) : [...p, id]);

  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    setSelectedServiceIds([]);
    setSelectedBusinessIds([]);
    reset();
  };

  const startEdit = (master: Master) => {
    setValue('name', master.name);
    setValue('phone', master.phone || '');
    setValue('telegram_id', String(master.telegram_id));
    setSelectedServiceIds(master.service_ids || []);
    setSelectedBusinessIds(master.business_ids || []);
    setEditingId(master.id);
    setShowForm(true);
  };

  const reloadMasters = async () => {
    const res = await mastersApi.getAll();
    setMasters(res.data);
  };

  const onSubmit = async (data: MasterFormData) => {
    setLoading(true);
    try {
      const payload: MasterPayload = {
        name: data.name,
        phone: data.phone || undefined,
        telegram_id: parseInt(data.telegram_id),
        service_ids: selectedServiceIds,
        business_ids: selectedBusinessIds,
      };

      if (editingId) {
        await mastersApi.update(editingId, payload);
        toast.success('Мастер обновлён');
      } else {
        await mastersApi.create(payload);
        toast.success('Мастер создан');
      }
      resetForm();
      await reloadMasters();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setLoading(false);
    }
  };

  const toggleBlock = async (master: Master) => {
    try {
      await mastersApi.update(master.id, { is_blocked: !master.is_blocked });
      toast.success(master.is_blocked ? 'Мастер разблокирован' : 'Мастер заблокирован');
      await reloadMasters();
    } catch { toast.error('Ошибка обновления статуса'); }
  };

  const getServiceNames = (ids: number[]): string[] =>
    ids.map((id) => services.find((s) => s.id === id)?.name).filter(Boolean) as string[];

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>Мастера</h1>
        <div className={styles.toolbar}>
          <select
            className={styles.filterSelect}
            value={filterBusinessId}
            onChange={(e) => setFilterBusinessId(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <option value="">Все салоны</option>
            {businesses.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          <button className={styles.primaryBtn} onClick={() => { resetForm(); setShowForm(true); }}>
            + Добавить мастера
          </button>
        </div>
      </div>

      {showForm && (
        <div className={styles.card}>
          <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Имя *</label>
              <input className={styles.input} {...register('name', { required: true })} placeholder="Анна Петрова" />
              {errors.name && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Telegram ID *</label>
              <input className={styles.input} type="number" {...register('telegram_id', { required: true })} placeholder="123456789" />
              {errors.telegram_id && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Телефон</label>
              <input className={styles.input} {...register('phone')} placeholder="+375..." />
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Услуги</label>
              <MultiSelectDropdown items={services} selectedIds={selectedServiceIds} onToggle={toggleService}
                getLabel={(s) => `${s.name} (${s.price} BYN)`} placeholder="Выберите услуги" />
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Салоны</label>
              <MultiSelectDropdown items={businesses} selectedIds={selectedBusinessIds} onToggle={toggleBusiness}
                getLabel={(b) => b.name} placeholder="Выберите салоны" />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" className={styles.primaryBtn} disabled={loading}>
                {loading ? 'Сохранение...' : editingId ? 'Обновить' : 'Создать'}
              </button>
              <button type="button" className={styles.secondaryBtn} onClick={resetForm}>Отмена</button>
            </div>
          </form>
        </div>
      )}

      <div className={styles.card}>
        {filteredMasters.length === 0 ? (
          <div className={styles.emptyState}>
            {masters.length === 0 ? 'Нет мастеров' : 'Нет мастеров в выбранном салоне'}
          </div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th><th>Имя</th><th>Telegram</th><th>Телефон</th>
                <th>Услуги</th><th>Статус</th><th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {filteredMasters.map((m) => {
                const serviceNames = getServiceNames(m.service_ids || []);
                return (
                  <tr key={m.id}>
                    <td>{m.id}</td>
                    <td>{m.name}</td>
                    <td>{m.telegram_id}</td>
                    <td>{m.phone || '-'}</td>
                    <td>
                      <div className={styles.tagList}>
                        {serviceNames.length > 0
                          ? serviceNames.map((n) => <span key={n} className={styles.tag}>{n}</span>)
                          : <span style={{ color: 'var(--text-muted)' }}>-</span>}
                      </div>
                    </td>
                    <td>
                      {m.is_blocked
                        ? <span className={styles.blockedBadge}>Заблокирован</span>
                        : <span className={styles.activeBadge}>Активен</span>}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button className={styles.secondaryBtn} onClick={() => startEdit(m)}>Изменить</button>
                        <button className={styles.dangerBtn} onClick={() => toggleBlock(m)}>
                          {m.is_blocked ? 'Разблок.' : 'Блок.'}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}