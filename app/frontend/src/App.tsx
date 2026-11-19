import { DisclaimerBar, NavBar } from './components/ui';
import { About } from './pages/About';
import { DataEntry } from './pages/DataEntry';
import { EcgPage } from './pages/EcgPage';
import { Home } from './pages/Home';
import { ModelCards } from './pages/ModelCards';
import { Results } from './pages/Results';
import { useSession } from './state/session';

export function App() {
  const { page } = useSession();
  return (
    <div className="min-h-screen">
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
        HealthRisk AI Research V2 · Phase XLV arayüzü · yalnız localhost · klinik karar aracı değildir
      </footer>
    </div>
  );
}
