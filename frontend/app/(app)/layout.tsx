"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuthActions, useCurrentUser } from "@/hooks/use-auth";
import { getToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/query", label: "Query" },
  { href: "/dashboards", label: "Dashboards" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { logout } = useAuthActions();
  const { data: user, isLoading, isError } = useCurrentUser();

  useEffect(() => {
    if (!getToken() || isError) router.replace("/login");
  }, [isError, router]);

  if (!getToken()) return null;

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-border px-6 py-3">
        <Link href="/query" className="text-sm font-semibold">
          InsightOps <span className="text-primary">AI</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-1.5 font-medium hover:bg-accent",
                pathname?.startsWith(item.href) && "bg-accent text-accent-foreground"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3 text-sm">
          {!isLoading && user && <span className="text-muted-foreground">{user.email}</span>}
          <Button variant="outline" size="sm" onClick={logout}>
            Log out
          </Button>
        </div>
      </header>
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
