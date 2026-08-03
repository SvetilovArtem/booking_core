export default function Dashboard() {
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '24px', color: 'var(--text-primary)' }}>
        Дашборд
      </h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
        <div style={{ padding: '20px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>Всего записей</h3>
          <p style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)' }}>0</p>
        </div>
        <div style={{ padding: '20px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>Выручка за месяц</h3>
          <p style={{ fontSize: '28px', fontWeight: 600, color: 'var(--text-primary)' }}>0 BYN</p>
        </div>
      </div>
    </div>
  );
}