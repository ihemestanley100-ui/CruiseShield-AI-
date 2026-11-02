/* Shared breadcrumb navigation. The last item is the current page
 * (no link, aria-current); earlier items link to existing routes. */

"use client";

import Link from "next/link";
import { useTranslation } from "../lib/i18n/context";

export interface Crumb {
  label: string;
  href?: string;
}

export function Breadcrumbs({ items }: { items: Crumb[] }) {
  const { t } = useTranslation("common");
  return (
    <nav aria-label={t("breadcrumb")}>
      <ol className="breadcrumbs">
        {items.map((item, index) => {
          const last = index === items.length - 1;
          return (
            <li key={index}>
              {last || item.href === undefined ? (
                <span aria-current={last ? "page" : undefined}>
                  {item.label}
                </span>
              ) : (
                <Link href={item.href}>{item.label}</Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
