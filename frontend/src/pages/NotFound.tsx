import { Link } from "react-router-dom";
import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-20 text-center sm:px-8" data-testid="not-found-panel">
      <p className="font-mono text-sm text-[#A3E635]">404</p>
      <h1 className="mt-2 text-3xl font-extrabold text-white">This page wandered off</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        The link may be stale — every provider has a fresh profile page.
      </p>
      <Link
        to="/"
        data-testid="not-found-home-link"
        className={`${buttonVariants({ variant: "outline" })} mt-6`}
      >
        Back to Sahaay home
      </Link>
    </div>
  );
}
