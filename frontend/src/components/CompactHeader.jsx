export default function CompactHeader() {
  return (
    <header className="compact-header">
      <div>
        <h1>WindLens</h1>
        <p className="compact-subtitle">UK Wind Forecast Performance</p>
      </div>
      <ul className="compact-meta" aria-label="Analysis context">
        <li>January 2026</li>
        <li className="compact-meta--emphasis">Historical analysis</li>
        <li>Source: Elexon</li>
      </ul>
    </header>
  );
}
