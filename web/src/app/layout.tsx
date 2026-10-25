import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import { AppNav, NavLinks } from "@/components/app-nav";
import { dataSource } from "@/lib/data";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: { default: "RewardLab", template: "%s · RewardLab" },
  description: "Reward hacking experiments for tool-using LLM agents.",
};

// Follow the OS color scheme before first paint (shadcn themes key off the .dark class).
const themeScript = `(() => {
  const m = matchMedia("(prefers-color-scheme: dark)");
  const apply = () => document.documentElement.classList.toggle("dark", m.matches);
  apply();
  m.addEventListener("change", apply);
})()`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="flex min-h-full flex-col md:flex-row">
        <aside className="flex items-center justify-between gap-4 border-b px-4 py-3 md:sticky md:top-0 md:h-screen md:w-56 md:flex-col md:items-stretch md:justify-start md:border-r md:border-b-0 md:py-5">
          <div className="space-y-0.5 md:px-2.5">
            <p className="font-semibold tracking-tight">RewardLab</p>
            <p className="hidden text-xs text-muted-foreground md:block">Reward hacking lab</p>
          </div>
          <Suspense fallback={<NavLinks pathname={null} />}>
            <AppNav />
          </Suspense>
          <p className="hidden text-xs text-muted-foreground md:mt-auto md:block md:px-2.5">
            Data: {dataSource === "api" ? "live API" : "mock fixtures"}
          </p>
        </aside>
        <main className="min-w-0 flex-1 px-4 py-6 md:px-8 md:py-8">{children}</main>
      </body>
    </html>
  );
}
