const CATEGORY_COLORS: Record<string, string> = {
  browse: "bg-accent-teal/10 text-accent-teal",
  auth: "bg-blue-50 text-blue-600",
  account: "bg-blue-50 text-blue-600",
  commerce: "bg-accent-amber-light text-amber-700",
  buy: "bg-accent-amber-light text-amber-700",
  support: "bg-green-50 text-green-700",
  legal: "bg-gray-100 text-gray-600",
  other: "bg-gray-100 text-gray-500",
};

export function CategoryPill({ category }: { category: string }) {
  const colors = CATEGORY_COLORS[category] ?? CATEGORY_COLORS.other;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors}`}
    >
      {category}
    </span>
  );
}
