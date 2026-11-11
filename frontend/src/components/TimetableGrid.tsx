import { motion } from "motion/react";
import { Sunrise, Sunset } from "lucide-react";
import { formatTime12, type Timetable, type TimetableSlot } from "@/lib/types";

const SLOT_STYLES = {
  available:
    "bg-emerald-950/70 hover:bg-emerald-900 border-emerald-500/60 text-emerald-300 shadow-[0_0_12px_rgba(34,197,94,0.15)] cursor-pointer active:scale-95",
  booked:
    "bg-rose-950/50 border-rose-500/40 text-rose-300/80 cursor-not-allowed",
  unavailable:
    "bg-slate-900/40 border border-slate-800 text-slate-500 cursor-not-allowed",
} as const;

const STATUS_LABEL = {
  available: "Available",
  booked: "Booked",
  unavailable: "Off-duty",
} as const;

function SlotButton({
  slot,
  onPick,
}: {
  slot: TimetableSlot;
  onPick: (slot: TimetableSlot) => void;
}) {
  const available = slot.status === "available";
  return (
    <motion.button
      type="button"
      whileTap={available ? { scale: 0.96 } : undefined}
      disabled={!available}
      onClick={() => available && onPick(slot)}
      data-testid={`slot-btn-${slot.start.replace(":", "-")}`}
      data-slot-status={slot.status}
      className={`flex min-h-[64px] flex-col items-center justify-center gap-0.5 rounded-xl border px-2 py-2 text-center transition-colors duration-150 ${SLOT_STYLES[slot.status]}`}
    >
      <span className="font-mono text-[13px] font-semibold">
        {formatTime12(slot.start)}
      </span>
      <span className="text-[11px] font-medium opacity-90">
        {STATUS_LABEL[slot.status]}
      </span>
    </motion.button>
  );
}

export default function TimetableGrid({
  timetable,
  onPick,
}: {
  timetable: Timetable | undefined;
  onPick: (slot: TimetableSlot) => void;
}) {
  if (!timetable) {
    return (
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4 md:grid-cols-6">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="h-16 animate-pulse rounded-xl bg-muted/50" />
        ))}
      </div>
    );
  }

  const slots = timetable.slots;
  const freeCount = slots.filter((s) => s.status === "available").length;
  const morning = slots.filter((s) => s.period === "morning");
  const evening = slots.filter((s) => s.period === "evening");

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="font-medium text-slate-300">
          {freeCount} of {slots.length} slots free
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Available — tap to book
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-rose-500" /> Booked / busy
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-slate-600" /> Off-duty
        </span>
      </div>

      {[
        { title: "Morning", icon: Sunrise, list: morning },
        { title: "Evening", icon: Sunset, list: evening },
      ].map(
        ({ title, icon: Icon, list }) =>
          list.length > 0 && (
            <section key={title}>
              <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-200">
                <Icon className="h-4 w-4 text-primary" /> {title}
              </h4>
              <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4 md:grid-cols-6 lg:gap-3">
                {list.map((slot) => (
                  <SlotButton key={slot.start} slot={slot} onPick={onPick} />
                ))}
              </div>
            </section>
          ),
      )}
    </div>
  );
}
