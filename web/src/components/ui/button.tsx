import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "outline";
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
        variant === "primary" &&
          "bg-slate-900 text-white hover:bg-slate-700",
        variant === "outline" &&
          "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50",
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
