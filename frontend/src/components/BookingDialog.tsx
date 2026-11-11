import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { CalendarDays, CheckCircle2, Clock3, Phone, Repeat } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiErrorMessage, apiPost } from "@/lib/api";
import {
  FREQUENCY_LABELS,
  WORK_TYPE_LABELS,
  formatTime12,
  type Booking,
  type Frequency,
  type Provider,
  type TimetableSlot,
} from "@/lib/types";

const FREQUENCY_OPTIONS: { id: Frequency; desc: string }[] = [
  { id: "one_time", desc: "Single session on the chosen date" },
  { id: "daily", desc: "Every day at this time slot" },
  { id: "weekly", desc: "Once every week on this day" },
];

export default function BookingDialog({
  provider,
  slot,
  date,
  dateLabel,
  open,
  onOpenChange,
  onBooked,
}: {
  provider: Provider;
  slot: TimetableSlot | null;
  date: string;
  dateLabel: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onBooked: () => void;
}) {
  const [consumerName, setConsumerName] = useState("");
  const [consumerPhone, setConsumerPhone] = useState("");
  const [frequency, setFrequency] = useState<Frequency>("one_time");
  const [confirmed, setConfirmed] = useState<Booking | null>(null);

  // Fresh form each time the dialog opens.
  useEffect(() => {
    if (open) {
      setConfirmed(null);
      setFrequency("one_time");
    }
  }, [open]);

  const bookingMutation = useMutation({
    mutationFn: (payload: {
      provider_id: string;
      date: string;
      slot_start: string;
      consumer_name: string;
      consumer_phone: string;
      frequency: Frequency;
    }) => apiPost<Booking>("/bookings", payload),
    onSuccess: (booking) => {
      setConfirmed(booking);
      onBooked();
      toast.success("Booking confirmed — the slot is yours!");
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  const pending = bookingMutation.isPending;

  const submit = () => {
    if (!slot) return;
    if (consumerName.trim().length < 2) {
      toast.error("Please enter your name.");
      return;
    }
    if (!/^(\+91[\-\s]?)?[6-9]\d{9}$/.test(consumerPhone.trim())) {
      toast.error("Please enter a valid 10-digit mobile number.");
      return;
    }
    bookingMutation.mutate({
      provider_id: provider.id,
      date,
      slot_start: slot.start,
      consumer_name: consumerName.trim(),
      consumer_phone: consumerPhone.trim(),
      frequency,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        {confirmed ? (
          <div className="space-y-4" data-testid="booking-success-panel">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-9 w-9 shrink-0 text-[#A3E635]" />
              <div>
                <DialogHeader>
                  <DialogTitle className="text-left">Request accepted!</DialogTitle>
                </DialogHeader>
                <DialogDescription className="text-left">
                  {provider.name} is booked for this slot.
                </DialogDescription>
              </div>
            </div>

            <div className="space-y-2 rounded-xl border border-slate-800 bg-muted/40 p-4 text-sm">
              <p className="flex items-center gap-2 text-slate-300">
                <CalendarDays className="h-4 w-4 text-primary" />
                {dateLabel} · {formatTime12(confirmed.slot_start)} – {formatTime12(confirmed.slot_end)}
              </p>
              <p className="flex items-center gap-2 text-slate-300">
                <Repeat className="h-4 w-4 text-primary" />
                {FREQUENCY_LABELS[confirmed.frequency]}
              </p>
              {confirmed.provider_phone && (
                <p className="flex items-center gap-2 text-slate-300">
                  <Phone className="h-4 w-4 text-[#A3E635]" />
                  <span className="font-mono font-semibold text-white" data-testid="booking-success-phone">
                    {confirmed.provider_phone}
                  </span>
                </p>
              )}
            </div>

            <p className="text-xs text-muted-foreground">
              Save this number — {provider.name} will call you to confirm details. For recurring
              bookings, this slot now shows as busy every {confirmed.frequency === "daily" ? "day" : "week"}.
            </p>

            <DialogFooter>
              <Button onClick={() => onOpenChange(false)} data-testid="booking-success-done-btn">
                Done
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="space-y-4">
            <DialogHeader>
              <DialogTitle>Book {provider.name}</DialogTitle>
              <DialogDescription>
                {WORK_TYPE_LABELS[provider.work_type ?? "cleaning"]} ·{" "}
                {dateLabel} · {slot ? `${formatTime12(slot.start)} – ${formatTime12(slot.end)}` : ""}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="booking-name">Your name</Label>
                <Input
                  id="booking-name"
                  value={consumerName}
                  onChange={(e) => setConsumerName(e.target.value)}
                  placeholder="e.g. Rohit Verma"
                  required
                  data-testid="booking-name-input"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="booking-phone">Your phone</Label>
                <Input
                  id="booking-phone"
                  type="tel"
                  value={consumerPhone}
                  onChange={(e) => setConsumerPhone(e.target.value)}
                  placeholder="98765 43210"
                  required
                  data-testid="booking-phone-input"
                />
              </div>

              <div className="space-y-1.5">
                <Label>
                  <Clock3 className="mr-1 inline h-3.5 w-3.5 text-primary" /> Repeat
                </Label>
                <div className="grid grid-cols-3 gap-2" data-testid="booking-frequency-group">
                  {FREQUENCY_OPTIONS.map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setFrequency(opt.id)}
                      data-testid={`booking-frequency-${opt.id}`}
                      aria-pressed={frequency === opt.id}
                      className={`rounded-xl border px-2 py-2.5 text-center transition-colors ${
                        frequency === opt.id
                          ? "border-primary bg-primary/15 text-white"
                          : "border-slate-800 bg-card text-slate-300 hover:border-slate-600"
                      }`}
                    >
                      <span className="block text-xs font-semibold">
                        {FREQUENCY_LABELS[opt.id]}
                      </span>
                      <span className="mt-0.5 block text-[10px] leading-tight text-muted-foreground">
                        {opt.desc}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="booking-cancel-btn">
                Cancel
              </Button>
              <Button onClick={submit} disabled={pending} data-testid="confirm-booking-btn">
                {pending ? "Booking…" : "Confirm booking"}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
