import type { Metadata } from "next";
import "@fontsource/geist-sans/400.css";
import "@fontsource/geist-sans/500.css";
import "@fontsource/geist-sans/700.css";
import "@fontsource/geist-mono/400.css";
import "@fontsource/geist-mono/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/700.css";
import "./globals.css";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { QueryProvider } from "@/lib/query-provider";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Header } from "@/components/layout/header";
import { StatusBar } from "@/components/layout/status-bar";

export const metadata: Metadata = {
  title: "MarketPulse AI",
  description: "Real-time financial sentiment intelligence platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full" suppressHydrationWarning>
      <body className="flex min-h-full w-full overflow-x-hidden flex-col font-sans">
        <ThemeProvider>
          <QueryProvider>
            <SidebarProvider>
              <AppSidebar />
              <div className="flex min-w-0 flex-1 flex-col overflow-x-hidden">
                <Header />
                <main className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden px-3 py-3 sm:p-4">
                  {children}
                </main>
                <StatusBar />
              </div>
            </SidebarProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
