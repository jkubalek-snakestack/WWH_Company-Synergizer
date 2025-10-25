import { cn } from "@/lib/utils";

export function Separator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("my-6 h-px w-full bg-border", className)}
      aria-hidden="true"
      {...props}
    />
  );
}
