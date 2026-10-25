import { AlertTriangle, CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

// Status is always icon + label, never color alone.

function Pill({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs font-medium whitespace-nowrap", className)}>
      {children}
    </span>
  );
}

export function VerifierStatus({ passed }: { passed: boolean | null }) {
  if (passed === null)
    return (
      <Pill className="text-muted-foreground">
        <CircleDashed className="size-3.5" /> Not verified
      </Pill>
    );
  return passed ? (
    <Pill>
      <CheckCircle2 className="size-3.5 text-status-good" /> Passed
    </Pill>
  ) : (
    <Pill>
      <XCircle className="size-3.5 text-status-critical" /> Failed
    </Pill>
  );
}

export function HackFlag({ isHack }: { isHack: boolean | null }) {
  if (!isHack) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <Pill>
      <AlertTriangle className="size-3.5 text-status-warning" /> Reward hack
    </Pill>
  );
}

export function RunSwatch({ color, className }: { color: string; className?: string }) {
  return <span aria-hidden className={cn("inline-block size-2.5 shrink-0 rounded-full", className)} style={{ background: color }} />;
}
