import { useEffect, useState, useMemo } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import toast from 'react-hot-toast';
import {
  format, startOfMonth, endOfMonth, eachDayOfInterval, getDay,
  addMonths, subMonths, isWithinInterval, isSameDay,
} from 'date-fns';
import { ru } from 'date-fns/locale';
import { slotsApi, type DayStats, type SlotBulkPayload } from '../../api/slots';
import { mastersApi, selectorsApi } from '../../api/masters';
import type { Master, Business } from '../../types';
import styles from './Slots.module.css';

type CalendarCell =
  | { empty: true; key: string; date?: undefined }
  | { empty: false; key: string; date: Date };

interface TimePeriod {
  startTime: string;
  endTime: string;
}

interface BulkForm {
  master_id: string;
  business_id: string;
  duration_minutes: number;
  periods: TimePeriod[];
}

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

/** Генерирует список времён с шагом из периодов */
function generateTimesFromPeriods(periods: TimePeriod[], slotMinutes: number): string[] {
  const times: string[] = [];
  for (const p of periods) {
    if (!p.startTime || !p.endTime) continue;
    const [sh, sm] = p.startTime.split(':').map(Number);
    const [eh, em] = p.endTime.split(':').map(Number);
    let cur = sh * 60 + sm;
    const end = eh * 60 + em;
    while (cur + slotMinutes <= end) {
      const h = Math.floor(cur / 60).toString().padStart(2, '0');
      const m = (cur % 60).toString().padStart(2, '0');
      times.push(`${h}:${m}`);
      cur += slotMinutes;
    }
  }
  return [...new Set(times)].sort();
}

/** Календарь выбора диапазона дат */
function DateRangePicker({
  dateFrom,
  dateTo,
  onChange,
}: {
  dateFrom: Date | null;
  dateTo: Date | null;
  onChange: (from: Date, to: Date) => void;
}) {
  const [viewMonth, setViewMonth] = useState(dateFrom || new Date());
  const [hoverDate, setHoverDate] = useState<Date | null>(null);
  // Флаг: если обе даты выбраны, следующий клик начинает новый выбор
  const [selectingEnd, setSelectingEnd] = useState(true);

  const days = useMemo((): CalendarCell[] => {
    const monthStart = startOfMonth(viewMonth);
    const monthEnd = endOfMonth(viewMonth);
    const allDays = eachDayOfInterval({ start: monthStart, end: monthEnd });
    const firstWeekday = (getDay(monthStart) + 6) % 7;
    const emptyBefore: CalendarCell[] = Array.from({ length: firstWeekday }, (_, i) => ({
      empty: true, key: `e-${i}`,
    }));
    const filled: CalendarCell[] = allDays.map((d) => ({
      empty: false, date: d, key: format(d, 'yyyy-MM-dd'),
    }));
    return [...emptyBefore, ...filled];
  }, [viewMonth]);

  const handleClick = (clicked: Date) => {
    if (!selectingEnd || !dateFrom) {
      // Начало нового выбора
      onChange(clicked, clicked);
      setSelectingEnd(true);
    } else {
      // Завершение диапазона
      const from = clicked < dateFrom ? clicked : dateFrom;
      const to = clicked < dateFrom ? dateFrom : clicked;
      onChange(from, to);
      setSelectingEnd(false);
    }
  };

  const getCellClass = (d: Date): string => {
    const classes = [styles.rangeCell];
    const isSelectedStart = dateFrom && isSameDay(d, dateFrom);
    const isSelectedEnd = dateTo && isSameDay(d, dateTo);
    const isSingle = dateFrom && dateTo && isSameDay(dateFrom, dateTo);

    if (isSingle && isSelectedStart) {
      classes.push(styles.rangeSingle);
    } else {
      if (isSelectedStart) classes.push(styles.rangeStart);
      if (isSelectedEnd) classes.push(styles.rangeEnd);
    }

    if (dateFrom && dateTo && !isSameDay(dateFrom, dateTo)) {
      if (isWithinInterval(d, { start: dateFrom, end: dateTo }) && !isSelectedStart && !isSelectedEnd) {
        classes.push(styles.rangeMiddle);
      }
    }

    // Превью при наведении
    if (selectingEnd && dateFrom && hoverDate) {
      const previewStart = hoverDate < dateFrom ? hoverDate : dateFrom;
      const previewEnd = hoverDate < dateFrom ? dateFrom : hoverDate;
      if (isWithinInterval(d, { start: previewStart, end: previewEnd }) && !isSelectedStart && !isSelectedEnd) {
        classes.push(styles.rangePreview);
      }
    }

    return classes.join(' ');
  };

  return (
    <div className={styles.rangePicker}>
      <div className={styles.calendarNav}>
        <button type="button" className={styles.navBtn} onClick={() => setViewMonth(subMonths(viewMonth, 1))}>←</button>
        <span className={styles.calendarTitle}>{format(viewMonth, 'LLLL yyyy', { locale: ru })}</span>
        <button type="button" className={styles.navBtn} onClick={() => setViewMonth(addMonths(viewMonth, 1))}>→</button>
      </div>
      <div className={styles.rangeGrid}>
        {WEEKDAYS.map((w) => <div key={w} className={styles.weekdayHeader}>{w}</div>)}
        {days.map((cell) => {
          if (cell.empty) return <div key={cell.key} className={styles.rangeCellEmpty} />;
          const cellDate = cell.date;
          return (
            <div
              key={cell.key}
              className={getCellClass(cellDate)}
              onClick={() => handleClick(cellDate)}
              onMouseEnter={() => setHoverDate(cellDate)}
              onMouseLeave={() => setHoverDate(null)}
            >
              {format(cellDate, 'd')}
            </div>
          );
        })}
      </div>
      <div className={styles.rangeHint}>
        {dateFrom && dateTo && !isSameDay(dateFrom, dateTo)
          ? `${format(dateFrom, 'dd.MM.yyyy')} — ${format(dateTo, 'dd.MM.yyyy')}`
          : dateFrom
            ? `${format(dateFrom, 'dd.MM.yyyy')} — выберите конечную дату`
            : 'Выберите начальную дату'}
      </div>
    </div>
  );
}

export default function Slots() {
  const [masters, setMasters] = useState<Master[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [stats, setStats] = useState<DayStats[]>([]);
  const [filterMasterId, setFilterMasterId] = useState<number | ''>('');
  const [filterBusinessId, setFilterBusinessId] = useState<number | ''>('');
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [rangeFrom, setRangeFrom] = useState<Date | null>(null);
  const [rangeTo, setRangeTo] = useState<Date | null>(null);

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<BulkForm>({
    defaultValues: {
      duration_minutes: 60,
      periods: [{ startTime: '09:00', endTime: '13:00' }, { startTime: '14:00', endTime: '18:00' }],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'periods' });

  useEffect(() => {
    Promise.all([
      mastersApi.getAll().catch(() => ({ data: [] as Master[] })),
      selectorsApi.getBusinesses().catch(() => ({ data: [] as Business[] })),
    ]).then(([mRes, bRes]) => {
      setMasters(mRes.data);
      setBusinesses(bRes.data);
    });
  }, []);

  useEffect(() => {
    const loadStats = async () => {
      const params: Record<string, string | number> = {
        date_from: format(startOfMonth(currentMonth), 'yyyy-MM-dd'),
        date_to: format(endOfMonth(currentMonth), 'yyyy-MM-dd'),
      };
      if (filterMasterId !== '') params.master_id = filterMasterId;
      if (filterBusinessId !== '') params.business_id = filterBusinessId;
      try {
        const res = await slotsApi.getStats(params);
        setStats(res.data);
      } catch { setStats([]); }
    };
    loadStats();
  }, [currentMonth, filterMasterId, filterBusinessId]);

  const statsMap = useMemo(() => {
    const map: Record<string, DayStats> = {};
    stats.forEach((s) => { map[s.date] = s; });
    return map;
  }, [stats]);

  const calendarDays = useMemo((): CalendarCell[] => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);
    const days = eachDayOfInterval({ start: monthStart, end: monthEnd });
    const firstDayWeekday = (getDay(monthStart) + 6) % 7;
    const emptyBefore: CalendarCell[] = Array.from({ length: firstDayWeekday }, (_, i) => ({
      empty: true, key: `empty-${i}`,
    }));
    const filled: CalendarCell[] = days.map((d) => ({
      empty: false, date: d, key: format(d, 'yyyy-MM-dd'),
    }));
    return [...emptyBefore, ...filled];
  }, [currentMonth]);

  const handleRangeChange = (from: Date, to: Date) => {
    setRangeFrom(from);
    setRangeTo(to);
  };

  const onSubmit = async (data: BulkForm) => {
    if (!data.master_id || !data.business_id) {
      toast.error('Выберите мастера и салон');
      return;
    }
    if (!rangeFrom || !rangeTo) {
      toast.error('Выберите диапазон дат в календаре');
      return;
    }
    const validPeriods = data.periods.filter((p) => p.startTime && p.endTime);
    if (validPeriods.length === 0) {
      toast.error('Добавьте хотя бы один временной период');
      return;
    }

    setLoading(true);
    try {
      const times = generateTimesFromPeriods(validPeriods, data.duration_minutes);
      if (times.length === 0) {
        toast.error('Нет валидных слотов для указанных периодов и размера');
        setLoading(false);
        return;
      }

      const payload: SlotBulkPayload = {
        master_id: parseInt(data.master_id),
        business_id: parseInt(data.business_id),
        date_from: format(rangeFrom, 'yyyy-MM-dd'),
        date_to: format(rangeTo, 'yyyy-MM-dd'),
        times,
        duration_minutes: data.duration_minutes,
      };

      const res = await slotsApi.createBulk(payload);
      toast.success(`Создано ${res.data.created} слотов${res.data.skipped > 0 ? `, пропущено ${res.data.skipped}` : ''}`);
      setShowForm(false);
      setRangeFrom(null);
      setRangeTo(null);
      reset();

      const params: Record<string, string | number> = {
        date_from: format(startOfMonth(currentMonth), 'yyyy-MM-dd'),
        date_to: format(endOfMonth(currentMonth), 'yyyy-MM-dd'),
      };
      if (filterMasterId !== '') params.master_id = filterMasterId;
      if (filterBusinessId !== '') params.business_id = filterBusinessId;
      const statsRes = await slotsApi.getStats(params);
      setStats(statsRes.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка создания слотов');
    } finally { setLoading(false); }
  };

  const todayStr = format(new Date(), 'yyyy-MM-dd');

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>Слоты</h1>
        <div className={styles.toolbar}>
          <select className={styles.filterSelect} value={filterBusinessId}
            onChange={(e) => setFilterBusinessId(e.target.value === '' ? '' : Number(e.target.value))}>
            <option value="">Все салоны</option>
            {businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
          <select className={styles.filterSelect} value={filterMasterId}
            onChange={(e) => setFilterMasterId(e.target.value === '' ? '' : Number(e.target.value))}>
            <option value="">Все мастера</option>
            {masters.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <button className={styles.primaryBtn} onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Отмена' : '+ Создать слоты'}
          </button>
        </div>
      </div>

      {showForm && (
        <div className={styles.card}>
          <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Мастер *</label>
              <select className={styles.input} {...register('master_id', { required: true })}>
                <option value="">Выберите мастера</option>
                {masters.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
              {errors.master_id && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>

            <div className={styles.inputGroup}>
              <label className={styles.label}>Салон *</label>
              <select className={styles.input} {...register('business_id', { required: true })}>
                <option value="">Выберите салон</option>
                {businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
              {errors.business_id && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Обязательное поле</span>}
            </div>

            {/* Календарь выбора диапазона */}
            <div className={styles.inputGroup}>
              <label className={styles.label}>Период дат *</label>
              <DateRangePicker dateFrom={rangeFrom} dateTo={rangeTo} onChange={handleRangeChange} />
            </div>

            {/* Временные периоды */}
            <div className={styles.inputGroup}>
              <label className={styles.label}>Временные окна *</label>
              {fields.map((field, index) => (
                <div key={field.id} className={styles.periodRow}>
                  <input type="time" className={styles.input} {...register(`periods.${index}.startTime`, { required: true })} />
                  <span style={{ color: 'var(--text-muted)' }}>—</span>
                  <input type="time" className={styles.input} {...register(`periods.${index}.endTime`, { required: true })} />
                  {fields.length > 1 && (
                    <button type="button" className={styles.removeBtn} onClick={() => remove(index)}>✕</button>
                  )}
                </div>
              ))}
              <button type="button" className={styles.secondaryBtn} onClick={() => append({ startTime: '', endTime: '' })} style={{ marginTop: 4 }}>
                + Добавить окно
              </button>
              {errors.periods && <span style={{ color: 'var(--danger)', fontSize: 12 }}>Заполните все периоды</span>}
            </div>

            {/* Размер слота */}
            <div className={styles.inputGroup}>
              <label className={styles.label}>Размер слота (мин) *</label>
              <select className={styles.input} {...register('duration_minutes', { valueAsNumber: true, required: true })}>
                <option value={15}>15 минут</option>
                <option value={30}>30 минут</option>
                <option value={45}>45 минут</option>
                <option value={60}>60 минут</option>
                <option value={90}>90 минут</option>
                <option value={120}>120 минут</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" className={styles.primaryBtn} disabled={loading}>
                {loading ? 'Создание...' : 'Создать слоты'}
              </button>
              <button type="button" className={styles.secondaryBtn} onClick={() => { setShowForm(false); setRangeFrom(null); setRangeTo(null); }}>
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Основной календарь статистики */}
      <div className={styles.card}>
        <div className={styles.calendarNav}>
          <button className={styles.navBtn} onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}>← Пред.</button>
          <span className={styles.calendarTitle}>{format(currentMonth, 'LLLL yyyy', { locale: ru })}</span>
          <button className={styles.navBtn} onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}>След. →</button>
        </div>
        <div className={styles.calendarGrid}>
          {WEEKDAYS.map((d) => <div key={d} className={styles.weekdayHeader}>{d}</div>)}
          {calendarDays.map((cell) => {
            if (cell.empty) return <div key={cell.key} className={`${styles.calendarCell} ${styles.empty}`} />;
            const dateStr = cell.key;
            const dayStats = statsMap[dateStr];
            const isToday = dateStr === todayStr;
            const cellDate = cell.date;
            return (
              <div key={cell.key} className={`${styles.calendarCell} ${isToday ? styles.today : ''}`}>
                <span className={styles.cellDate}>{format(cellDate, 'd')}</span>
                <div className={styles.cellStats}>
                  {dayStats ? (
                    <>
                      <div className={styles.statAvailable}>Свободно: {dayStats.available}</div>
                      <div className={styles.statBooked}>Занято: {dayStats.booked}</div>
                    </>
                  ) : (
                    <div className={styles.statEmpty}>Нет слотов</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}