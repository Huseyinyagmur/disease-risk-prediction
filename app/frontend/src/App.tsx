import { useState } from 'react';
import { AssistantPanel } from './components/AssistantPanel';
import { DisclaimerBar, NavBar } from './components/ui';
import { About } from './pages/About';
import { DataEntry } from './pages/DataEntry';
import { EcgPage } from './pages/EcgPage';
import { Home } from './pages/Home';
import { ModelCards } from './pages/ModelCards';
import { Results } from './pages/Results';
import { t } from './lib/ui';
import { useSession } from './state/session';

export function App() {
  const { page, schema } = useSession();
  // Phase L: asistan yan paneli açıkken (masaüstü) tüm içerik — uyarı bandı dahil — panel kadar daralır; uyarı görünür kalır.
  const [asstPad, setAsstPad] = useState(0);
  return (
    <div className="min-h-screen" style={asstPad ? { marginRight: asstPad } : undefined} data-testid="app-shell">
      <DisclaimerBar />
      <NavBar />
      <main className="mx-auto max-w-7xl px-4 py-6">
        {page === 'home' && <Home />}
        {page === 'form' && <DataEntry />}
        {page === 'results' && <Results />}
        {page === 'ecg' && <EcgPage />}
        {page === 'models' && <ModelCards />}
        {page === 'about' && <About />}
      </main>
      <footer className="border-t border-slate-200 py-3 text-center text-[11px] text-slate-500">
        {t(schema, 'footer')}
      </footer>
      <AssistantPanel onLayout={setAsstPad} />
    </div>
  );
}
