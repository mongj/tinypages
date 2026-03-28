import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-border bg-bg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-1 text-lg font-semibold">
          <span className="text-accent-teal">tiny</span>
          <span className="text-text-primary">pages</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm text-text-secondary">
          <Link href="/" className="hover:text-text-primary transition-colors">
            Sites
          </Link>
        </nav>
      </div>
    </header>
  );
}
