import { Link, NavLink } from "react-router-dom";
import { HeartHandshake } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";

export default function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-[#080B10]/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-8 sm:py-3.5">
        <Link to="/" className="flex items-center gap-2.5" data-testid="header-brand">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-primary/15 ring-1 ring-primary/40">
            <HeartHandshake className="h-5 w-5 text-primary" />
            <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-[#A3E635] ring-2 ring-[#080B10]" />
          </span>
          <span className="flex flex-col leading-none">
            <span className="text-lg font-extrabold tracking-tight text-white">Sahaay</span>
            <span className="text-[11px] font-medium text-muted-foreground">
              your neighbourhood, on call
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          <NavLink
            to="/browse"
            data-testid="header-link-browse"
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? "text-white" : "text-slate-400 hover:text-white"
              }`
            }
          >
            Browse providers
          </NavLink>
          <NavLink
            to="/register"
            data-testid="header-link-register"
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? "text-white" : "text-slate-400 hover:text-white"
              }`
            }
          >
            For providers
          </NavLink>
        </nav>

        <div className="flex items-center gap-2">
          <Link
            to="/browse"
            data-testid="header-cta-find-help"
            className={buttonVariants({ variant: "default", size: "sm" })}
          >
            Find help
          </Link>
          <Link
            to="/register"
            data-testid="header-cta-register"
            className={`${buttonVariants({ variant: "outline", size: "sm" })} border-[#84CC16]/40 text-[#A3E635] hover:bg-[#84CC16]/10 hover:text-[#BEF264]`}
          >
            List a service
          </Link>
        </div>
      </div>
    </header>
  );
}
