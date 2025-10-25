import Link from "next/link";

import { Button } from "@/components/ui/button";

const featuredCards = [
  {
    title: "Narrative Ingestion",
    description:
      "Turn free-form company stories into structured profiles using OpenAI-powered parsing.",
    action: {
      label: "View API Docs",
      href: "https://github.com/WWH-Inc/synergizer"
    }
  },
  {
    title: "Synergy Graph",
    description:
      "Visualize cross-company relationships, readiness signals, and policy-driven rankings.",
    action: {
      label: "Launch Graph Service",
      href: "http://localhost:8000/docs"
    }
  },
  {
    title: "Playbook Templates",
    description:
      "Customize WWH 9 Keys-aligned playbooks and share them with partner cohorts.",
    action: {
      label: "Browse Templates",
      href: "#templates"
    }
  }
];

export default function HomePage() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16">
      <section className="grid gap-6 md:grid-cols-2 md:items-center">
        <div className="space-y-6">
          <span className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-xs font-semibold uppercase tracking-wide text-secondary-foreground">
            WWH Company Synergizer
          </span>
          <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-5xl">
            Align every WWH partner around actionable collaboration opportunities.
          </h1>
          <p className="text-base text-muted-foreground md:text-lg">
            Curate company narratives, quantify capabilities, and surface the high-impact
            cross-company initiatives that drive WWH&apos;s Nine Keys.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link href="/auth/login">Sign in</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/docs/getting-started">Read the playbook</Link>
            </Button>
          </div>
        </div>
        <div className="grid gap-4 rounded-xl border bg-card/50 p-6 shadow-sm backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Quick Actions
          </p>
          <div className="grid gap-3">
            {featuredCards.map((card) => (
              <div
                key={card.title}
                className="flex flex-col gap-2 rounded-lg border border-border/60 bg-background/80 p-4 transition hover:border-primary/60 hover:shadow"
              >
                <div>
                  <h3 className="text-lg font-semibold">{card.title}</h3>
                  <p className="text-sm text-muted-foreground">{card.description}</p>
                </div>
                <div>
                  <Button asChild size="sm" variant="ghost">
                    <Link href={card.action.href}>{card.action.label}</Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
