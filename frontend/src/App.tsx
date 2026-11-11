import { useEffect } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import SiteHeader from "@/components/SiteHeader";
import Home from "@/pages/Home";
import Browse from "@/pages/Browse";
import ProviderDetail from "@/pages/ProviderDetail";
import Register from "@/pages/Register";
import NotFound from "@/pages/NotFound";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground">
      <ScrollToTop />
      <SiteHeader />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/browse" element={<Browse />} />
          <Route path="/provider/:id" element={<ProviderDetail />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="border-t border-slate-800/80 py-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-4 text-center text-xs text-muted-foreground sm:px-8">
          <p>
            <Link to="/" className="font-semibold text-slate-300 hover:text-white" data-testid="footer-brand">
              Sahaay
            </Link>{" "}
            · local services for your neighbourhood · built with a Flask REST API + React
          </p>
          <p>No Aadhaar, ever. Maid phone numbers stay masked until a booking is confirmed.</p>
        </div>
      </footer>
      <Toaster />
    </div>
  );
}
