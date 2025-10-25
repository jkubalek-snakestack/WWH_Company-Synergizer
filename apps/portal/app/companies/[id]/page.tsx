import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { updateOpportunityStatusAction } from "@/server/actions/opportunity";
import { createCaller } from "@/server/trpc/caller";

function formatList(values: string[]): string {
  return values.length ? values.join(", ") : "—";
}

export default async function CompanyPage({
  params,
}: {
  params: { id: string };
}) {
  const caller = await createCaller();

  const company = await caller.companies
    .byId({ id: params.id })
    .catch(() => null);

  if (!company) {
    notFound();
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-8">
      <section className="flex flex-col gap-4">
        <div>
          <h1 className="text-3xl font-semibold">{company.name}</h1>
          <p className="text-muted-foreground">
            {company.mission ?? "Mission to be provided."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">Region:</span>
          <span>{company.region ?? "Global"}</span>
          <Separator className="mx-1 h-4 w-px" />
          <span className="font-medium text-foreground">WWH Keys:</span>
          <div className="flex flex-wrap gap-2">
            {company.wwhKeys.length ? (
              company.wwhKeys.map((key) => (
                <Badge key={key} variant="secondary">
                  {key}
                </Badge>
              ))
            ) : (
              <span>Unspecified</span>
            )}
          </div>
        </div>
        {company.capabilities.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Capabilities:</span>
            <div className="flex flex-wrap gap-2">
              {company.capabilities.map((capability) => (
                <Badge key={capability} variant="outline">
                  {capability}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Needs</CardTitle>
            <CardDescription>Areas where support is requested.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {company.needs.length ? (
              company.needs.map((need) => (
                <div key={need.id} className="rounded-md border border-border p-4">
                  <h3 className="font-medium">{need.title}</h3>
                  {need.description && (
                    <p className="text-sm text-muted-foreground">{need.description}</p>
                  )}
                  <p className="mt-2 text-xs text-muted-foreground">
                    Urgency: <span className="font-medium text-foreground">{need.urgency}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Visibility: {need.visibility}
                  </p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Tags: <span className="font-medium text-foreground">{formatList(need.tags)}</span>
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No active needs.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Offers</CardTitle>
            <CardDescription>Value the company is ready to provide.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {company.offers.length ? (
              company.offers.map((offer) => (
                <div key={offer.id} className="rounded-md border border-border p-4">
                  <h3 className="font-medium">{offer.title}</h3>
                  {offer.description && (
                    <p className="text-sm text-muted-foreground">{offer.description}</p>
                  )}
                  <p className="mt-2 text-xs text-muted-foreground">
                    Capacity: <span className="font-medium text-foreground">{offer.capacity}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Visibility: {offer.visibility}
                  </p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Tags: <span className="font-medium text-foreground">{formatList(offer.tags)}</span>
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No current offers.</p>
            )}
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Key Contacts</CardTitle>
          <CardDescription>Coordinators who can facilitate collaboration.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {company.contacts.length ? (
            company.contacts.map((contact) => (
              <div key={contact.id} className="rounded-md border border-border p-4">
                <h3 className="font-medium">{contact.name}</h3>
                {contact.role && (
                  <p className="text-sm text-muted-foreground">{contact.role}</p>
                )}
                <div className="mt-2 text-xs text-muted-foreground">
                  <p>Privacy: {contact.privacyLevel}</p>
                  {contact.email && <p>Email: {contact.email}</p>}
                  {contact.phone && <p>Phone: {contact.phone}</p>}
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No contacts listed.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Opportunities</CardTitle>
          <CardDescription>
            Manage and archive opportunities for this company.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Summary</TableHead>
                <TableHead>Partner</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Score</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {company.opportunities.map((opportunity) => {
                const partner =
                  opportunity.source.id === company.id
                    ? opportunity.target
                    : opportunity.source;
                const isArchived = opportunity.status === "ARCHIVED";
                return (
                  <TableRow key={opportunity.id}>
                    <TableCell className="max-w-[260px]">
                      <div className="flex flex-col gap-1">
                        <span className="font-medium">
                          {opportunity.need?.title ?? opportunity.offer?.title ?? "Opportunity"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {opportunity.breakdown?.summary ?? "Synergy recommendation"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button asChild variant="link" className="px-0">
                        <Link href={`/companies/${partner.id}`}>{partner.name}</Link>
                      </Button>
                    </TableCell>
                    <TableCell>
                      <Badge variant={isArchived ? "outline" : "secondary"}>
                        {opportunity.status.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-semibold">
                      {opportunity.score.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right">
                      <form action={updateOpportunityStatusAction} className="inline">
                        <input type="hidden" name="opportunityId" value={opportunity.id} />
                        <input type="hidden" name="companyId" value={company.id} />
                        <input
                          type="hidden"
                          name="status"
                          value={isArchived ? "OPEN" : "ARCHIVED"}
                        />
                        <Button variant="outline" size="sm" type="submit">
                          {isArchived ? "Restore" : "Archive"}
                        </Button>
                      </form>
                    </TableCell>
                  </TableRow>
                );
              })}
              {company.opportunities.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No opportunities yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </main>
  );
}
