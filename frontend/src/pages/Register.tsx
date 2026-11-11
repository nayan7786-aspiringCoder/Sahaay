import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { motion } from "motion/react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Hammer,
  HeartHandshake,
  Sparkles,
  Wrench,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiErrorMessage, apiPost } from "@/lib/api";
import { type Category, type Provider, type WorkType } from "@/lib/types";

const CATEGORY_CARDS: { id: Category; label: string; desc: string; icon: typeof Wrench }[] = [
  { id: "maid", label: "Maid", desc: "Cleaning, cooking or both — with morning/evening hours", icon: HeartHandshake },
  { id: "electrician", label: "Electrician", desc: "Wiring, repairs, appliances & fittings", icon: Wrench },
  { id: "carpenter", label: "Carpenter", desc: "Furniture, doors, modular woodwork", icon: Hammer },
  { id: "other", label: "Other local service", desc: "Plumber, painter, tutor — any local skill", icon: Sparkles },
];

export default function Register() {
  const [category, setCategory] = useState<Category | null>(null);
  const [created, setCreated] = useState<Provider | null>(null);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [workType, setWorkType] = useState<WorkType>("cleaning");
  const [morningAvailable, setMorningAvailable] = useState(true);
  const [morningStart, setMorningStart] = useState("07:00");
  const [morningEnd, setMorningEnd] = useState("11:00");
  const [eveningAvailable, setEveningAvailable] = useState(false);
  const [eveningStart, setEveningStart] = useState("17:00");
  const [eveningEnd, setEveningEnd] = useState("21:00");
  const [wantsRegular, setWantsRegular] = useState(true);
  const [specialty, setSpecialty] = useState("");
  const [shopAddress, setShopAddress] = useState("");

  const registerMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost<Provider>("/providers", payload),
    onSuccess: (provider) => {
      setCreated(provider);
      toast.success("You're listed on Sahaay!");
      window.scrollTo(0, 0);
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!category) return;

    const payload: Record<string, unknown> =
      category === "maid"
        ? {
            name,
            phone,
            category,
            work_type: workType,
            morning_available: morningAvailable,
            morning_start: morningStart,
            morning_end: morningEnd,
            evening_available: eveningAvailable,
            evening_start: eveningStart,
            evening_end: eveningEnd,
            wants_regular: wantsRegular,
          }
        : {
            name,
            phone,
            category,
            specialty,
            shop_address: shopAddress,
          };
    registerMutation.mutate(payload);
  };

  if (created) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-14 sm:px-8" data-testid="register-success-panel">
        <Card className="border-[#84CC16]/40 bg-card text-center">
          <CardContent className="p-10">
            <CheckCircle2 className="mx-auto h-14 w-14 text-[#A3E635]" />
            <h1 className="mt-4 text-2xl font-extrabold text-white">
              You're listed, {created.name.split(" ")[0]}!
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">
              Households can now find you on Sahaay
              {created.category === "maid"
                ? " and book your free timetable slots — one-time, daily or weekly."
                : " and reach you on your listed phone number."}
            </p>
            {created.category === "maid" && created.phone_masked && (
              <p className="mt-3 text-xs text-muted-foreground">
                Your number shows publicly as <span className="font-mono">{created.phone_masked}</span>{" "}
                — the full number is shared only after a household books you.
              </p>
            )}
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link
                to={`/provider/${created.id}`}
                data-testid="register-view-profile"
                className="inline-flex items-center gap-1 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary/90"
              >
                View my public profile <ArrowRight className="h-4 w-4" />
              </Link>
              <Button
                variant="outline"
                data-testid="register-another-btn"
                onClick={() => {
                  setCreated(null);
                  setCategory(null);
                  setName("");
                  setPhone("");
                  setSpecialty("");
                  setShopAddress("");
                }}
              >
                Register another provider
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!category) {
    return (
      <div className="mx-auto max-w-4xl px-4 pb-16 sm:px-8">
        <header className="pt-8 sm:pt-12">
          <Badge variant="outline" className="border-primary/40 bg-primary/10 text-[#93C5FD]">
            Provider registration
          </Badge>
          <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            What service do you provide?
          </h1>
          <p className="mt-2 text-sm text-slate-300">
            Pick your category — the form adapts to what matters for your work.
          </p>
        </header>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {CATEGORY_CARDS.map(({ id, label, desc, icon: Icon }) => (
            <motion.button
              key={id}
              type="button"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setCategory(id)}
              data-testid={`provider-category-${id}`}
              className="flex items-start gap-4 rounded-2xl border border-slate-800 bg-card p-5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/60 hover:shadow-[0_12px_24px_rgba(37,99,235,0.12)]"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/15 ring-1 ring-primary/40">
                <Icon className="h-5 w-5 text-primary" />
              </span>
              <span>
                <span className="block font-semibold text-white">{label}</span>
                <span className="mt-1 block text-sm text-slate-400">{desc}</span>
              </span>
            </motion.button>
          ))}
        </div>
      </div>
    );
  }

  const isMaid = category === "maid";
  const categoryLabel = CATEGORY_CARDS.find((c) => c.id === category)?.label ?? "";

  return (
    <div className="mx-auto max-w-2xl px-4 pb-16 sm:px-8">
      <button
        type="button"
        onClick={() => setCategory(null)}
        className="mt-6 inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-white"
        data-testid="register-back-to-categories"
      >
        <ArrowLeft className="h-4 w-4" /> Change category
      </button>

      <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-white">
        Register as a {categoryLabel.toLowerCase()}
      </h1>

      <form onSubmit={submit} className="mt-6 space-y-5" data-testid="register-form">
        <Card className="border-slate-800 bg-card">
          <CardContent className="space-y-4 p-6">
            <div className="space-y-1.5">
              <Label htmlFor="register-name">Your name</Label>
              <Input
                id="register-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Sunita Devi"
                required
                minLength={2}
                maxLength={80}
                data-testid="register-name-input"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="register-phone">Phone number</Label>
              <Input
                id="register-phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="98765 43210"
                required
                data-testid="register-phone-input"
              />
              <p className="text-xs text-muted-foreground">
                {isMaid
                  ? "Shown publicly only in masked form; shared fully after a booking is confirmed."
                  : "Visible to households so they can call you directly."}
              </p>
            </div>
          </CardContent>
        </Card>

        {isMaid ? (
          <Card className="border-slate-800 bg-card" data-testid="register-maid-section">
            <CardContent className="space-y-5 p-6">
              <div className="space-y-1.5">
                <Label>Type of work</Label>
                <div className="grid grid-cols-3 gap-2" data-testid="register-work-type-group">
                  {(["cleaning", "cooking", "both"] as WorkType[]).map((wt) => (
                    <button
                      key={wt}
                      type="button"
                      onClick={() => setWorkType(wt)}
                      data-testid={`register-work-type-${wt}`}
                      aria-pressed={workType === wt}
                      className={`rounded-xl border px-3 py-2.5 text-sm font-medium transition-colors ${
                        workType === wt
                          ? "border-primary bg-primary/15 text-white"
                          : "border-slate-800 text-slate-300 hover:border-slate-600"
                      }`}
                    >
                      {wt === "cleaning" ? "House cleaning" : wt === "cooking" ? "Cooking" : "Both"}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 p-4" data-testid="register-morning-shift">
                <label className="flex items-center gap-3">
                  <Checkbox
                    checked={morningAvailable}
                    onCheckedChange={(checked) => setMorningAvailable(checked === true)}
                    data-testid="register-morning-available"
                  />
                  <span className="text-sm font-semibold text-white">Morning availability</span>
                </label>
                {morningAvailable && (
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="register-morning-start">Start (06:00–12:00)</Label>
                      <Input
                        id="register-morning-start"
                        type="time"
                        value={morningStart}
                        min="06:00"
                        max="12:00"
                        onChange={(e) => setMorningStart(e.target.value)}
                        required
                        data-testid="register-morning-start"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="register-morning-end">End</Label>
                      <Input
                        id="register-morning-end"
                        type="time"
                        value={morningEnd}
                        min="06:00"
                        max="12:00"
                        onChange={(e) => setMorningEnd(e.target.value)}
                        required
                        data-testid="register-morning-end"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-slate-800 p-4" data-testid="register-evening-shift">
                <label className="flex items-center gap-3">
                  <Checkbox
                    checked={eveningAvailable}
                    onCheckedChange={(checked) => setEveningAvailable(checked === true)}
                    data-testid="register-evening-available"
                  />
                  <span className="text-sm font-semibold text-white">Evening availability</span>
                </label>
                {eveningAvailable && (
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="register-evening-start">Start (12:00–21:00)</Label>
                      <Input
                        id="register-evening-start"
                        type="time"
                        value={eveningStart}
                        min="12:00"
                        max="21:00"
                        onChange={(e) => setEveningStart(e.target.value)}
                        required
                        data-testid="register-evening-start"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="register-evening-end">End</Label>
                      <Input
                        id="register-evening-end"
                        type="time"
                        value={eveningEnd}
                        min="12:00"
                        max="21:00"
                        onChange={(e) => setEveningEnd(e.target.value)}
                        required
                        data-testid="register-evening-end"
                      />
                    </div>
                  </div>
                )}
              </div>

              <label className="flex items-start gap-3" data-testid="register-wants-regular-row">
                <Checkbox
                  checked={wantsRegular}
                  onCheckedChange={(checked) => setWantsRegular(checked === true)}
                  data-testid="register-wants-regular"
                />
                <span className="text-sm text-slate-300">
                  I'd like <span className="font-semibold text-white">regular / recurring</span>{" "}
                  household work, not just one-time jobs
                </span>
              </label>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-slate-800 bg-card" data-testid="register-trades-section">
            <CardContent className="space-y-4 p-6">
              <div className="space-y-1.5">
                <Label htmlFor="register-specialty">Specialty</Label>
                <Input
                  id="register-specialty"
                  value={specialty}
                  onChange={(e) => setSpecialty(e.target.value)}
                  placeholder={
                    category === "electrician"
                      ? "e.g. House wiring, inverter & MCB repair"
                      : category === "carpenter"
                        ? "e.g. Modular kitchens & wardrobe repair"
                        : "e.g. Plumber — taps, tanks & bathroom fitting"
                  }
                  required
                  minLength={3}
                  maxLength={120}
                  data-testid="register-specialty-input"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="register-shop-address">Shop address</Label>
                <Textarea
                  id="register-shop-address"
                  value={shopAddress}
                  onChange={(e) => setShopAddress(e.target.value)}
                  placeholder="e.g. Shop 12, Vijay Nagar Market, Indore"
                  required
                  minLength={5}
                  maxLength={200}
                  rows={3}
                  data-testid="register-shop-address-input"
                />
                <p className="text-xs text-muted-foreground">
                  Shown on your public profile so customers can find your shop.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={registerMutation.isPending}
          data-testid="register-submit-btn"
        >
          {registerMutation.isPending ? "Listing you…" : "List my service on Sahaay"}
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          We never ask for Aadhaar or any government ID — listing is free and instant.
        </p>
      </form>
    </div>
  );
}
