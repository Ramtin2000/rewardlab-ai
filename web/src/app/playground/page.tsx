import type { Metadata } from "next";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { dataSource, getPlaygroundModels } from "@/lib/data";
import { PlaygroundForm } from "./playground-form";

export const metadata: Metadata = { title: "Playground" };

async function Playground() {
  const models = await getPlaygroundModels();
  return <PlaygroundForm models={models} />;
}

export default function Page() {
  return (
    <>
      <PageHeader
        title="Playground"
        description={
          dataSource === "api"
            ? "Run one SupportDesk episode against the live environment and inspect the trace."
            : "Run one SupportDesk episode and inspect the trace. Using scripted mock agents until the backend is connected."
        }
      />
      <Suspense fallback={<Skeleton className="h-24 w-full" />}>
        <Playground />
      </Suspense>
    </>
  );
}
