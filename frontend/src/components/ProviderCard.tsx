import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { Clock3, MapPin, Phone, Repeat, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  CATEGORY_LABELS,
  WORK_TYPE_LABELS,
  formatTime12,
  nameSlug,
  type Provider,
} from "@/lib/types";

export default function ProviderCard({ provider }: { provider: Provider }) {
  const slug = nameSlug(provider.name);
  const isMaid = provider.category === "maid";
  const initials = provider.name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      whileHover={{ y: -4 }}
      className="h-full"
    >
      <Link
        to={`/provider/${provider.id}`}
        data-testid={`provider-card-${slug}`}
        className="flex h-full flex-col rounded-2xl border border-slate-800 bg-card p-5 transition-[border-color,box-shadow] duration-200 hover:border-primary/60 hover:shadow-[0_12px_24px_rgba(37,99,235,0.12)]"
      >
        <div className="flex items-start gap-3">
          <span
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-bold ring-1 ${
              isMaid
                ? "bg-[#84CC16]/10 text-[#BEF264] ring-[#84CC16]/40"
                : "bg-primary/10 text-[#93C5FD] ring-primary/40"
            }`}
          >
            {initials}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="truncate font-semibold text-white">{provider.name}</h3>
              {provider.verified && (
                <ShieldCheck className="h-4 w-4 shrink-0 text-[#A3E635]" aria-label="Verified" />
              )}
            </div>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {CATEGORY_LABELS[provider.category]}
              {isMaid && provider.work_type ? ` · ${WORK_TYPE_LABELS[provider.work_type]}` : ""}
            </p>
          </div>
        </div>

        {!isMaid && provider.specialty && (
          <p className="mt-3 line-clamp-2 text-sm text-slate-300">{provider.specialty}</p>
        )}

        <div className="mt-3 flex flex-wrap gap-1.5">
          {provider.morning_available && (
            <Badge variant="secondary" className="gap-1 bg-secondary/80">
              <Clock3 className="h-3 w-3" /> Morning {formatTime12(provider.morning_start)} –{" "}
              {formatTime12(provider.morning_end)}
            </Badge>
          )}
          {provider.evening_available && (
            <Badge variant="secondary" className="gap-1 bg-secondary/80">
              <Clock3 className="h-3 w-3" /> Evening {formatTime12(provider.evening_start)} –{" "}
              {formatTime12(provider.evening_end)}
            </Badge>
          )}
          {isMaid && (
            <Badge
              variant="outline"
              className={`gap-1 ${provider.wants_regular ? "border-[#84CC16]/40 text-[#A3E635]" : "border-slate-700 text-slate-400"}`}
            >
              <Repeat className="h-3 w-3" />
              {provider.wants_regular ? "Prefers regular work" : "On-demand ok"}
            </Badge>
          )}
        </div>

        {!isMaid && (
          <div className="mt-3 space-y-1 text-sm text-slate-300">
            {provider.phone && (
              <p className="flex items-center gap-2" data-testid={`provider-card-phone-${slug}`}>
                <Phone className="h-3.5 w-3.5 shrink-0 text-primary" />
                <span className="font-mono text-[13px]">{provider.phone}</span>
              </p>
            )}
            {provider.shop_address && (
              <p className="flex items-start gap-2">
                <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                <span className="line-clamp-2">{provider.shop_address}</span>
              </p>
            )}
          </div>
        )}

        <p
          className={`mt-4 border-t border-slate-800 pt-3 text-sm font-semibold ${
            isMaid ? "text-primary" : "text-[#A3E635]"
          }`}
        >
          {isMaid ? "View timetable & book →" : "Call & view details →"}
        </p>
      </Link>
    </motion.div>
  );
}
