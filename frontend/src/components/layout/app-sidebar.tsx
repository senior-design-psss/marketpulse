"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Brain,
  Building2,
  LayoutDashboard,
  Radio,
  Settings,
  Share2,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const navItems = [
  { title: "DASH", desc: "Dashboard", href: "/", icon: LayoutDashboard },
  { title: "SECT", desc: "Industries", href: "/industries", icon: Building2 },
  { title: "EQTY", desc: "Companies", href: "/companies", icon: BarChart3 },
  { title: "TOP", desc: "Live Feed", href: "/feed", icon: Radio },
  { title: "AI", desc: "Analyst", href: "/analyst", icon: Brain },
  { title: "GRAPH", desc: "Entity Map", href: "/graph", icon: Share2 },
  { title: "CTRL", desc: "Control Panel", href: "/admin", icon: Settings },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-[#1E1E1E] px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-[#FFA028]" />
          <div>
            <span className="font-mono text-sm font-bold text-[#FFA028]">
              MARKETPULSE
            </span>
            <span className="ml-1 font-mono text-[10px] text-[#4AF6C3]">AI</span>
          </div>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="font-mono text-[10px] uppercase tracking-widest text-[#FFA028]">
            Functions
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    render={<Link href={item.href} />}
                    isActive={
                      item.href === "/"
                        ? pathname === "/"
                        : pathname.startsWith(item.href)
                    }
                  >
                    <item.icon className="h-4 w-4" />
                    <span className="font-mono">
                      <span className="font-bold text-[#FEE334]">{item.title}</span>
                      <span className="ml-2 text-xs text-muted-foreground">{item.desc}</span>
                    </span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
