import { useCallback, useEffect, useRef, useState } from 'react';
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
  // Phase L2: asistan kipli çekmece/iletişim kutusudur; açıkken arka plan (uyarı şeridi dahil) inert olur, içerik daralmaz.
  const shell = useRef<HTMLDivElement>(null);
  const [asstOpen, setAsstOpen] = useState(false);
  const onAsst = useCallback((o: boolean) => setAsstOpen(o), []);
  useEffect(() => {
    shell.current?.toggleAttribute('inert', asstOpen);
  }, [asstOpen]);
  return (
    <>
      <div ref={shell} className="min-h-screen" data-testid="app-shell">
        <DisclaimerBar />
        <NavBar />
        <main className="mx-auto max-w-6xl px-4 pb-24 pt-6 sm:px-6">
          {page === 'home' && <Home />}
          {page === 'form' && <DataEntry />}
          {page === 'results' && <Results />}
          {page === 'ecg' && <EcgPage />}
          {page === 'models' && <ModelCards />}
          {page === 'about' && <About />}
        </main>
        <footer className="border-t border-slate-200 py-3 text-center text-xs text-slate-500">{t(schema, 'footer')}</footer>
      </div>
      <AssistantPanel onOpenChange={onAsst} />
    </>
  );
}
