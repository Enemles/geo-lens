import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "positive" | "muted";
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        tone === "neutral" && "bg-slate-100 text-slate-700",
        tone === "positive" && "bg-teal-50 text-teal-700",
        tone === "muted" && "bg-slate-100 text-slate-400",
        className,
      )}
      {...props}
    />
  );
}
