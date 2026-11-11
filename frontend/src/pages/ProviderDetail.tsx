import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  Clock3,
  Copy,
  MapPin,
  Phone,
  Repeat,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import TimetableGrid from "@/components/TimetableGrid";
import BookingDialog from "@/components/BookingDialog";
import { apiErrorMessage, apiGet } from "@/lib/api";
import {
  CATEGORY_LABELS,
  WORK_TYPE_LABELS,
  type Meta,
  type Provider,
  type Timetable,
  type TimetableSlot,
} from "@/lib/types";

export default function ProviderDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [date, setDate] = useState<string | null>(null);
  const [slot, setSlot] = useState<TimetableSlot | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const providerQuery = useQuery({
    queryKey: ["provider", id],
    queryFn: () => apiGet<Provider>(`/providers/${id}`),
    enabled: !!id,
    retry: false,
  });
  const metaQuery = useQuery({
    queryKey: ["meta"],
    queryFn: () => apiGet<Meta>("/meta"),
    retry: false,
  });

  const activeDate = date ?? metaQuery.data?.today ?? "";
  const timetableQuery = useQuery({
    queryKey: ["timetable", id, activeDate],
    queryFn: () => apiGet<Timetable>(`/providers/${id}/timetable?date=${activeDate}`),
    enabled: !!id && !!activeDate,
    placeholderData: (prev) => prev,
  });

  if (providerQuery.isPending) {
    return (
      <div className="mx-auto max-w-6xl space-y-4 px-4 py-10 sm:px-8">
        <div className="h-10 w-64 animate-pulse rounded-xl bg-muted/50" />
        <div className="h-64 animate-pulse rounded-2xl bg-muted/40" />
      </div>
    );
  }

  if (providerQuery.isError) {
    const notFound = apiErrorMessage(providerQuery.error).includes("No provider");
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center sm:px-8" data-testid="provider-error-panel">
        <p className="text-lg font-semibold text-white">
          {notFound ? "This provider isn't listed anymore." : "Couldn't reach the Sahaay service."}
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          {notFound
            ? "The profile may have been removed."
            : "Check your connection and try again in a moment."}
        </p>
        <Link
          to="/browse"
          data-testid="provider-back-to-browse"
          className={`${buttonVariants({ variant: "outline" })} mt-6`}
        >
          <ArrowLeft className="mr-1 h-4 w-4" /> Back to all providers
        </Link>
      </div>
    );
  }

  const provider = providerQuery.data!;
  const isMaid = provider.category === "maid";
  const dateLabel =
    metaQuery.data?.week.find((d) => d.date === activeDate)?.label ?? activeDate;

  const pickSlot = (picked: TimetableSlot) => {
    setSlot(picked);
    setDialogOpen(true);
  };

  const copyAddress = async () => {
    await navigator.clipboard.writeText(provider.shop_address ?? "");
    toast.success("Shop address copied");
  };

  return (
    <div className="mx-auto max-w-6xl px-4 pb-16 sm:px-8">
      <Link
        to="/browse"
        className="mt-6 inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-white"
        data-testid="provider-back-link"
      >
        <ArrowLeft className="h-4 w-4" /> All providers
      </Link>

      {/* Profile header */}
      <Card className="mt-4 border-slate-800 bg-card">
        <CardContent className="flex flex-col gap-5 p-6 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
                {provider.name}
              </h1>
              {provider.verified && (
                <Badge
                  variant="outline"
                  className="gap-1 border-[#84CC16]/40 text-[#BEF264]"
                  data-testid="provider-verified-badge"
                >
                  <ShieldCheck className="h-3.5 w-3.5" /> Verified
                </Badge>
              )}
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
              <Badge variant="secondary" className="bg-primary/15 text-[#93C5FD]">
                {CATEGORY_LABELS[provider.category]}
              </Badge>
              {isMaid && provider.work_type && (
                <Badge variant="secondary" className="bg-secondary">
                  {WORK_TYPE_LABELS[provider.work_type]}
                </Badge>
              )}
              {!isMaid && provider.specialty && (
                <Badge variant="secondary" className="bg-secondary">
                  {provider.specialty}
                </Badge>
              )}
              {isMaid && (
                <Badge
                  variant="outline"
                  className={`gap-1 ${provider.wants_regular ? "border-[#84CC16]/40 text-[#A3E635]" : "border-slate-700 text-slate-400"}`}
                  data-testid="provider-regular-badge"
                >
                  <Repeat className="h-3 w-3" />
                  {provider.wants_regular ? "Prefers regular / recurring work" : "On-demand ok"}
                </Badge>
              )}
            </div>

            <div className="mt-4 grid gap-2 text-sm text-slate-300 sm:grid-cols-2">
              <p className="flex items-center gap-2" data-testid="provider-morning-hours">
                <Clock3 className="h-4 w-4 text-primary" />
                Morning:{" "}
                {provider.morning_available
                  ? `${provider.morning_start} – ${provider.morning_end}`
                  : "not available"}
              </p>
              <p className="flex items-center gap-2" data-testid="provider-evening-hours">
                <Clock3 className="h-4 w-4 text-primary" />
                Evening:{" "}
                {provider.evening_available
                  ? `${provider.evening_start} – ${provider.evening_end}`
                  : "not available"}
              </p>
            </div>
          </div>

          <div className="shrink-0 space-y-3 sm:w-64">
            {isMaid ? (
              <div
                className="rounded-xl border border-slate-800 bg-muted/40 p-4 text-xs leading-relaxed text-muted-foreground"
                data-testid="provider-maid-privacy-note"
              >
                <Phone className="mb-1 h-4 w-4 text-[#A3E635]" />
                <p className="font-mono">{provider.phone_masked}</p>
                <p className="mt-1">
                  {provider.name.split(" ")[0]}'s number is shared right after your booking is
                  confirmed — no spam, no directories.
                </p>
              </div>
            ) : (
              <div className="space-y-2" data-testid="provider-trades-contact">
                <a
                  href={`tel:${provider.phone}`}
                  data-testid="provider-call-btn"
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary/90"
                >
                  <Phone className="h-4 w-4" /> Call {provider.name.split(" ")[0]}
                </a>
                {provider.shop_address && (
                  <div className="rounded-xl border border-slate-800 bg-muted/40 p-4 text-xs text-muted-foreground">
                    <p className="flex items-start gap-2 text-sm text-slate-200">
                      <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      {provider.shop_address}
                    </p>
                    <Button
                      variant="outline"
                      size="xs"
                      className="mt-2 w-full"
                      onClick={copyAddress}
                      data-testid="provider-copy-address-btn"
                    >
                      <Copy className="mr-1 h-3 w-3" /> Copy address
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {isMaid && (
        <Card className="mt-6 border-slate-800 bg-card" data-testid="provider-timetable-card">
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center justify-between gap-3">
              <span>Timetable · {dateLabel}</span>
              <div className="flex flex-wrap gap-1.5" data-testid="provider-day-strip">
                {metaQuery.data?.week.map((day) => (
                  <button
                    key={day.date}
                    type="button"
                    onClick={() => setDate(day.date)}
                    data-testid={`day-pill-${day.date}`}
                    aria-pressed={day.date === activeDate}
                    className={`rounded-lg border px-2.5 py-1.5 font-mono text-xs transition-colors ${
                      day.date === activeDate
                        ? "border-primary bg-primary/20 text-white"
                        : "border-slate-800 text-slate-400 hover:border-slate-600 hover:text-white"
                    }`}
                  >
                    {day.label}
                  </button>
                ))}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TimetableGrid timetable={timetableQuery.data} onPick={pickSlot} />
          </CardContent>
        </Card>
      )}

      {isMaid && (
        <BookingDialog
          provider={provider}
          slot={slot}
          date={activeDate}
          dateLabel={dateLabel}
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          onBooked={() => {
            queryClient.invalidateQueries({ queryKey: ["timetable", id] });
            queryClient.invalidateQueries({ queryKey: ["providers"] });
          }}
        />
      )}

      {!isMaid && (
        <p className="mt-6 text-xs text-muted-foreground" data-testid="provider-trades-note">
          Tradespeople take calls directly — call ahead, describe the job, and agree a time.
          Maids on Sahaay, by contrast, take bookings through their live timetable.
        </p>
      )}
    </div>
  );
}
