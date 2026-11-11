import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  ArrowRight,
  CalendarCheck,
  ClipboardList,
  Search,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { apiGet } from "@/lib/api";
import { type ProviderList } from "@/lib/types";

export default function Home() {
  // Live counts for the hero strip. If the backend is unreachable (static
  // preview), the page still renders — the numbers simply show as dashes.
  const { data } = useQuery({
    queryKey: ["providers", "all"],
    queryFn: () => apiGet<ProviderList>("/providers"),
    retry: false,
  });

  const providers = data?.providers ?? [];
  const maids = providers.filter((p) => p.category === "maid").length;
  const trades = providers.length - maids;

  const stats = [
    { label: "Providers listed", value: providers.length },
    { label: "Maids on Sahaay", value: maids },
    { label: "Electricians, carpenters & more", value: trades },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 pb-16 sm:px-8">
      <section className="pt-10 sm:pt-16">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="max-w-3xl"
        >
          <Badge
            variant="outline"
            className="gap-1.5 border-primary/40 bg-primary/10 text-[#93C5FD]"
            data-testid="home-eyebrow-badge"
          >
            <ShieldCheck className="h-3.5 w-3.5" /> Now live in your neighbourhood
          </Badge>
          <h1 className="mt-4 text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
            Trusted local help,
            <br />
            <span className="text-[#A3E635]">on your schedule.</span>
          </h1>
          <p className="mt-4 text-base leading-relaxed text-slate-300 sm:text-lg">
            Sahaay connects households with verified maids, electricians, carpenters and
            neighbourhood helpers. Check morning &amp; evening hours, tap a free slot, and
            your booking is confirmed instantly.
          </p>
        </motion.div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.05 }}
          >
            <Link
              to="/browse"
              data-testid="home-choice-looking"
              className="group flex h-full flex-col rounded-2xl border border-primary/50 bg-card p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary hover:shadow-[0_12px_32px_rgba(37,99,235,0.18)]"
            >
              <Badge variant="secondary" className="w-fit bg-primary/15 text-[#93C5FD]">
                For households &amp; residents
              </Badge>
              <h2 className="mt-4 text-2xl font-bold text-white">I'm looking for a service</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-300">
                Find trusted maids for cooking &amp; cleaning, electricians, carpenters and
                reliable neighbourhood helpers. Filter by hours and book recurring help.
              </p>
              <span
                className={`${buttonVariants({ variant: "default" })} mt-5 w-fit group-hover:translate-x-0.5`}
                data-testid="home-choice-looking-cta"
              >
                Browse local providers <ArrowRight className="ml-1 h-4 w-4" />
              </span>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Link
              to="/register"
              data-testid="home-choice-provider"
              className="group flex h-full flex-col rounded-2xl border border-[#84CC16]/40 bg-card p-6 transition-all duration-200 hover:-translate-y-1 hover:border-[#A3E635] hover:shadow-[0_12px_32px_rgba(132,204,22,0.15)]"
            >
              <Badge variant="secondary" className="w-fit bg-[#84CC16]/15 text-[#BEF264]">
                For maids &amp; tradespeople
              </Badge>
              <h2 className="mt-4 text-2xl font-bold text-white">I provide a service</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-300">
                List your skills, set your morning &amp; evening availability, receive
                bookings for one-time or recurring work — and grow your local client base.
              </p>
              <span
                className={`${buttonVariants({ variant: "outline" })} mt-5 w-fit border-[#84CC16]/50 text-[#BEF264] hover:bg-[#84CC16]/10 hover:text-[#BEF264] group-hover:translate-x-0.5`}
                data-testid="home-choice-provider-cta"
              >
                Register your profile <ArrowRight className="ml-1 h-4 w-4" />
              </span>
            </Link>
          </motion.div>
        </div>
      </section>

      <section className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-3" data-testid="home-stats">
        {stats.map((stat) => (
          <Card key={stat.label} size="sm" className="bg-card/70">
            <CardContent className="py-4">
              <p className="text-2xl font-extrabold text-white" data-testid="home-stat-value">
                {data ? stat.value : "—"}
              </p>
              <p className="mt-0.5 text-xs font-medium text-muted-foreground">{stat.label}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="mt-12" id="how-it-works">
        <h2 className="text-xl font-bold text-white sm:text-2xl">How it works</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          {[
            {
              icon: Search,
              title: "Pick a category",
              desc: "Maid, electrician, carpenter or another local skill — then filter by specialty and shift.",
            },
            {
              icon: CalendarCheck,
              title: "Check the timetable",
              desc: "Green slots are free — tap one, choose one-time, daily or weekly, and send your request.",
            },
            {
              icon: ShieldCheck,
              title: "Confirmed instantly",
              desc: "Requests are auto-accepted, the slot locks as busy, and you get the provider's number.",
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="rounded-2xl border border-slate-800 bg-card/60 p-5">
              <Icon className="h-5 w-5 text-primary" />
              <h3 className="mt-3 font-semibold text-white">{title}</h3>
              <p className="mt-1 text-sm leading-relaxed text-slate-400">{desc}</p>
            </div>
          ))}
        </div>
        <p className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
          <ClipboardList className="h-4 w-4" />
          Privacy first: we never ask for Aadhaar or ID numbers. A maid's phone number is
          shared only after your booking is confirmed.
        </p>
      </section>
    </div>
  );
}
