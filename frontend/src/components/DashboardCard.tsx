interface DashboardCardProps {
  title: string;
  value: string;
  trend?: string;
  isPositive?: boolean;
}

export default function DashboardCard({ title, value, trend, isPositive }: DashboardCardProps) {
  return (
    <div className="card">
      <h3 className="card-title">{title}</h3>
      <p className="card-value">{value}</p>
      {trend && (
        <div className={`card-trend ${isPositive ? 'trend-up' : 'trend-down'}`}>
          {isPositive ? '▲' : '▼'} {trend}
        </div>
      )}
    </div>
  );
}
