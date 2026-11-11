import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ProviderCard from "@/components/ProviderCard";
import { apiGet } from "@/lib/api";
import { CATEGORY_LABELS, type Category, type ProviderList, type WorkType } from "@/lib/types";

type CategoryFilter = "all" | Category;

export default function Browse() {
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [workType, setWorkType] = useState<WorkType | "">("");
  const [shift, setShift] = useState<"" | "morning" | "evening">("");
  const [regular, setRegular] = useState<boolean | null>(null);
  const [q, setQ] = useState("");

  const params = new URLSearchParams();
  if (category !== "all") params.set("category", category);
  if (workType) params.set("work_type", workType);
  if (shift) params.set("shift", shift);
  if (regular !== null) params.set("regular", String(regular));
  if (q.trim()) params.set("q", q.trim());
  const qs = params.toString();

  const { data, isPending } = useQuery({
    queryKey: ["providers", { category, workType, shift, regular, q }],
    queryFn: () => apiGet<ProviderList>(`/providers${qs ? `?${qs}` : ""}`),
    placeholderData: (prev) => prev,
  });

  const providers = data?.providers ?? [];
  const hasFilters = category !== "all" || !!workType || !!shift || regular !== null || !!q.trim();

  const clearFilters = () => {
    setCategory("all");
    setWorkType("");
    setShift("");
    setRegular(null);
    setQ("");
  };

  return (
    <div className="mx-auto max-w-6xl px-4 pb-16 sm:px-8">
      <header className="pt-8 sm:pt-10">
        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
          Browse local providers
        </h1>
        <p className="mt-2 text-sm text-slate-300 sm:text-base">
          Maids with live timetables, plus electricians, carpenters and other trusted
          neighbourhood services.
        </p>
      </header>

      <div className="mt-6 space-y-3 rounded-2xl border border-slate-800 bg-card/60 p-4">
        <Tabs
          value={category}
          onValueChange={(value) => setCategory(value as CategoryFilter)}
          data-testid="browse-category-tabs"
        >
          <TabsList className="flex w-full flex-wrap gap-1">
            <TabsTrigger value="all" data-testid="filter-category-all">
              All
            </TabsTrigger>
            <TabsTrigger value="maid" data-testid="filter-category-maid">
              Maids
            </TabsTrigger>
            <TabsTrigger value="electrician" data-testid="filter-category-electrician">
              Electricians
            </TabsTrigger>
            <TabsTrigger value="carpenter" data-testid="filter-category-carpenter">
              Carpenters
            </TabsTrigger>
            <TabsTrigger value="other" data-testid="filter-category-other">
              Other services
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-2 rounded-lg border border-slate-800 bg-background px-3 py-1.5">
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search name or specialty…"
              data-testid="browse-search-input"
              className="w-44 bg-transparent text-sm text-white placeholder:text-muted-foreground focus:outline-none sm:w-56"
            />
          </label>

          {(category === "all" || category === "maid") &&
            (["cleaning", "cooking", "both"] as WorkType[]).map((wt) => (
              <button
                key={wt}
                type="button"
                onClick={() => setWorkType(workType === wt ? "" : wt)}
                data-testid={`filter-work-type-${wt}`}
                aria-pressed={workType === wt}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                  workType === wt
                    ? "border-primary bg-primary/20 text-white"
                    : "border-slate-800 text-slate-300 hover:border-slate-600"
                }`}
              >
                {wt === "cleaning" ? "House cleaning" : wt === "cooking" ? "Cooking" : "Cleaning & Cooking"}
              </button>
            ))}

          {(["morning", "evening"] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setShift(shift === s ? "" : s)}
              data-testid={`filter-shift-${s}`}
              aria-pressed={shift === s}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                shift === s
                  ? "border-primary bg-primary/20 text-white"
                  : "border-slate-800 text-slate-300 hover:border-slate-600"
              }`}
            >
              {s} shift
            </button>
          ))}

          <button
            type="button"
            onClick={() => setRegular(regular === true ? null : true)}
            data-testid="filter-regular"
            aria-pressed={regular === true}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              regular === true
                ? "border-[#84CC16] bg-[#84CC16]/15 text-[#BEF264]"
                : "border-slate-800 text-slate-300 hover:border-slate-600"
            }`}
          >
            Regular work preferred
          </button>

          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters} data-testid="browse-clear-filters">
              <SlidersHorizontal className="mr-1 h-3.5 w-3.5" /> Clear
            </Button>
          )}
        </div>
      </div>

      <p className="mt-5 text-sm text-muted-foreground" data-testid="browse-result-count">
        {isPending ? "Loading providers…" : `${providers.length} provider${providers.length === 1 ? "" : "s"} found`}
      </p>

      {isPending ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-52 animate-pulse rounded-2xl bg-muted/40" />
          ))}
        </div>
      ) : providers.length > 0 ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {providers.map((provider) => (
            <ProviderCard key={provider.id} provider={provider} />
          ))}
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-dashed border-slate-800 p-10 text-center">
          <p className="font-semibold text-white">No providers match these filters</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try clearing a filter or searching for a different specialty.
          </p>
          {hasFilters && (
            <Button variant="outline" size="sm" className="mt-4" onClick={clearFilters} data-testid="browse-empty-clear-btn">
              Clear all filters
            </Button>
          )}
        </div>
      )}

    </div>
  );
}
