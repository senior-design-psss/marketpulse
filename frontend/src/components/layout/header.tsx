"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "./theme-toggle";
import { GoBar } from "./go-bar";

export function Header() {
  return (
    <header className="flex h-10 min-w-0 items-center gap-2 border-b border-border bg-[#0D1117] px-3 sm:gap-3 sm:px-4 dark:bg-[#0D1117]">
      <SidebarTrigger className="shrink-0" />
      <Separator orientation="vertical" className="hidden h-5 sm:block" />
      <GoBar />
      <Separator orientation="vertical" className="hidden h-5 sm:block" />
      <ThemeToggle />
    </header>
  );
}
