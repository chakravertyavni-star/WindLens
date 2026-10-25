const NAV = [
  { id: "overview", label: "Overview" },
  { id: "forecast", label: "Forecast Analysis" },
  { id: "methodology", label: "Methodology" },
];

export default function Sidebar({ active, onNavigate }) {
  return (
    <aside className="sidebar" aria-label="Primary">
      <div className="sidebar-brand">
        <span className="sidebar-logo">WindLens</span>
      </div>
      <nav className="sidebar-nav">
        <ul>
          {NAV.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={`sidebar-link ${active === item.id ? "is-active" : ""}`}
                onClick={() => onNavigate(item.id)}
                aria-current={active === item.id ? "page" : undefined}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
