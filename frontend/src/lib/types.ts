// Hand-written mirrors of the Flask JSON responses — nothing infers across the
// HTTP boundary, so keep these in sync with backend/sahaay/routes/*.py.

export type Category = "maid" | "electrician" | "carpenter" | "other";
export type WorkType = "cleaning" | "cooking" | "both";
export type Frequency = "one_time" | "daily" | "weekly";
export type SlotStatus = "available" | "booked" | "unavailable";
export type BookingStatus = "accepted" | "declined" | "cancelled";

export interface Provider {
  id: string;
  name: string;
  category: Category;
  specialty: string | null;
  work_type: WorkType | null;
  // Tradespeople list their phone publicly; maids expose phone_masked until a
  // booking is confirmed (then provider_phone rides on the booking response).
  phone?: string | null;
  phone_masked?: string;
  shop_address?: string | null;
  morning_available: boolean;
  morning_start: string | null;
  morning_end: string | null;
  evening_available: boolean;
  evening_start: string | null;
  evening_end: string | null;
  wants_regular: boolean;
  verified: boolean;
  created_at: string;
}

export interface TimetableSlot {
  start: string;
  end: string;
  period: "morning" | "evening";
  status: SlotStatus;
}

export interface Timetable {
  provider: Provider;
  date: string;
  weekday: number;
  slots: TimetableSlot[];
}

export interface Booking {
  id: string;
  provider_id: string;
  provider_name: string | null;
  provider_phone?: string | null;
  provider_specialty?: string | null;
  consumer_name: string;
  consumer_phone: string;
  date: string;
  weekday: number;
  period: string;
  slot_start: string;
  slot_end: string;
  frequency: Frequency;
  status: BookingStatus;
  created_at: string;
}

export interface ProviderList {
  providers: Provider[];
  count: number;
}

export interface BookingList {
  bookings: Booking[];
  count: number;
}

export interface WeekDay {
  date: string;
  weekday: number;
  label: string;
}

export interface Meta {
  categories: { id: Category; label: string }[];
  work_types: { id: WorkType; label: string }[];
  frequencies: { id: Frequency; label: string }[];
  bookings_auto_accept: boolean;
  today: string;
  week: WeekDay[];
  store: string;
}

export interface Health {
  status: string;
  store: string;
  store_detail: string;
  sheets_configured: boolean;
  time: string;
}

// ---- labels & formatting helpers ----

export const CATEGORY_LABELS: Record<Category, string> = {
  maid: "Maid",
  electrician: "Electrician",
  carpenter: "Carpenter",
  other: "Local Service",
};

export const WORK_TYPE_LABELS: Record<WorkType, string> = {
  cleaning: "House cleaning",
  cooking: "Cooking",
  both: "Cleaning & Cooking",
};

export const FREQUENCY_LABELS: Record<Frequency, string> = {
  one_time: "One-time service",
  daily: "Daily recurring",
  weekly: "Weekly recurring",
};

export const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function formatTime12(t?: string | null): string {
  if (!t) return "—";
  const [h, m] = t.split(":").map(Number);
  const suffix = h >= 12 ? "PM" : "AM";
  const hr = h % 12 === 0 ? 12 : h % 12;
  return `${hr}:${String(m).padStart(2, "0")} ${suffix}`;
}

export function nameSlug(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}


