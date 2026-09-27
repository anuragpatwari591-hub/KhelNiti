import Link from "next/link";
import type { ReactNode } from "react";
import { useTheme } from "@/lib/theme";

export default function Layout({ children }: { children: ReactNode }) {
  const { theme, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-surface text-ink">
      <header className="border-b border-black/10 dark:border-white/10">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            KhelNiti
          </Link>
          <nav className="flex items-center gap-4 text-sm text-ink-muted">
            <Link href="/?sport=cricket" className="hover:text-ink">
              Cricket
            </Link>
            <Link href="/?sport=football" className="hover:text-ink">
              Football
            </Link>
            <button
              onClick={toggle}
              aria-label="Toggle theme"
              className="rounded-full border border-black/10 px-3 py-1 hover:text-ink dark:border-white/10"
            >
              {theme === "light" ? "Dark" : "Light"}
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
    </div>
  );
}
