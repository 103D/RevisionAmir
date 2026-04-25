import { Suspense, lazy } from 'react';

import './App.css';

const FilialsPage = lazy(() => import('./components/FilialsPage'));

/**
 * Main Application Component
 * Root layout with header and content area
 */
function App() {
  return (
    <div className="app">
      {/* ============================================================
          Header Section
          ============================================================ */}
      <header className="header">
        <div>
          <p className="kicker">Revision Workspace</p>
          <h1 className="title">Ревизии филиалов</h1>
          <p className="subtitle">Следующая дата, перенос и итоговая недостача в одном месте.</p>
        </div>
      </header>

      {/* ============================================================
          Main Content Area
          ============================================================ */}
      <main className="main">
        <Suspense fallback={<div className="systemState">Загрузка приложения...</div>}>
          <FilialsPage />
        </Suspense>
      </main>
    </div>
  );
}

export default App;
