import Sidebar from '../components/Sidebar';
import DashboardCard from '../components/DashboardCard';

export default function Home() {
  return (
    <div className="layout-container">
      <Sidebar />
      <main className="main-content">
        <header className="header">
          <h1>Executive Dashboard</h1>
          <p>Real-time overview of your competitive landscape.</p>
        </header>

        <div className="dashboard-grid">
          <DashboardCard title="Total Locations Monitored" value="1,204" trend="12 this week" isPositive={true} />
          <DashboardCard title="Avg Competitor Rating" value="4.2" trend="0.1 from last month" isPositive={false} />
          <DashboardCard title="AI Health Score" value="94 / 100" trend="Top 5% in Region" isPositive={true} />
          <DashboardCard title="Active Alerts" value="3" trend="Needs attention" isPositive={false} />
        </div>

        <section style={{ marginTop: '3rem' }}>
          <h2>AI Insights Feed</h2>
          <div className="glass-panel" style={{ padding: '1.5rem', marginTop: '1rem' }}>
            <h4 style={{ color: 'var(--primary-accent)', margin: '0 0 0.5rem 0' }}>Opportunity Detected</h4>
            <p style={{ margin: 0, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Gemini Insight: A major competitor in the Northside district has seen a 15% drop in sentiment over the last 14 days, primarily due to service speed complaints. This presents an opportunity to capture local traffic with targeted "fast service" promotions.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
