import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { ChevronLeft } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { RunSwatch } from "@/components/status";
import { TrajectoryView } from "@/components/trajectory-view";
import { getRun, getTrajectory } from "@/lib/data";
import { runColor } from "@/lib/format";

async function Detail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const trajectory = await getTrajectory(id);
  if (!trajectory) notFound();
  const run = await getRun(trajectory.run_id);

  return (
    <>
      <PageHeader title={trajectory.episode_id}>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span className="flex items-center gap-2">
            {run && <RunSwatch color={runColor(run)} />}
            {run?.name ?? trajectory.run_id}
          </span>
          <span>Step {trajectory.checkpoint_step}</span>
          <span>Seed {trajectory.seed}</span>
          <span className="font-mono text-xs">{trajectory.model}</span>
        </div>
      </PageHeader>
      <TrajectoryView trajectory={trajectory} />
    </>
  );
}

export default function Page(props: PageProps<"/trajectories/[id]">) {
  return (
    <>
      <Link href="/trajectories" className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft className="size-4" /> All trajectories
      </Link>
      <Suspense fallback={<Skeleton className="h-96 w-full" />}>
        <Detail params={props.params} />
      </Suspense>
    </>
  );
}
