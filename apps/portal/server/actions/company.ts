"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";

import { companyProfileSchema } from "@/lib/schema";
import { slugify } from "@/lib/utils";
import { requireUser } from "../auth";
import { prisma } from "../db/client";

const payloadSchema = companyProfileSchema.extend({
  narrative: z.string().optional(),
});

const GRAPH_SERVICE_URL =
  process.env.GRAPH_SERVICE_URL ?? "http://localhost:8000";

export type CreateCompanyInput = z.infer<typeof payloadSchema>;

async function triggerGraphRecompute(orgId: string) {
  const companies = await prisma.company.findMany({
    where: { orgId },
    include: {
      tags: { include: { tag: true } },
      needs: true,
      offers: true,
      contacts: true,
    },
  });

  const dataset = {
    companies: companies.map((company) => ({
      id: company.id,
      orgId: company.orgId,
      slug: slugify(company.name),
      name: company.name,
      region: company.region ?? undefined,
      mission: company.mission ?? undefined,
      wwhKeys: company.wwhKeys,
      capabilities: company.tags.map(({ tag }) => tag.name),
      visibility: company.visibility,
    })),
    needs: companies.flatMap((company) =>
      company.needs.map((need) => ({
        id: need.id,
        companyId: need.companyId,
        title: need.title,
        description: need.description ?? undefined,
        tags: need.tags,
        urgency: need.urgency,
        visibility: need.visibility,
      })),
    ),
    offers: companies.flatMap((company) =>
      company.offers.map((offer) => ({
        id: offer.id,
        companyId: offer.companyId,
        title: offer.title,
        description: offer.description ?? undefined,
        tags: offer.tags,
        capacity: offer.capacity,
        visibility: offer.visibility,
      })),
    ),
    contacts: companies.flatMap((company) =>
      company.contacts.map((contact) => ({
        id: contact.id,
        companyId: contact.companyId,
        name: contact.name,
        role: contact.role ?? undefined,
        email: contact.email ?? undefined,
        phone: contact.phone ?? undefined,
        privacyLevel: contact.privacyLevel,
      })),
    ),
  };

  try {
    await fetch(`${GRAPH_SERVICE_URL}/recompute`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(dataset),
    });
  } catch (error) {
    console.error("Graph recompute failed", error);
  }
}

export async function createCompanyAction(rawInput: CreateCompanyInput) {
  const user = await requireUser();
  const input = payloadSchema.parse(rawInput);

  const company = await prisma.company.create({
    data: {
      orgId: user.orgId,
      name: input.company.name,
      region: input.company.region ?? undefined,
      mission: input.company.mission ?? undefined,
      wwhKeys: input.company.wwhKeys,
      tags: {
        connectOrCreate: input.company.capabilities.map((capability) => ({
          where: { slug: slugify(capability) },
          create: {
            orgId: user.orgId,
            name: capability,
            slug: slugify(capability),
          },
        })),
      },
      needs: {
        create: input.needs.map((need) => ({
          title: need.title,
          description: need.description ?? undefined,
          tags: need.tags,
          urgency: need.urgency,
          visibility: need.visibility,
        })),
      },
      offers: {
        create: input.offers.map((offer) => ({
          title: offer.title,
          description: offer.description ?? undefined,
          tags: offer.tags,
          capacity: offer.capacity,
          visibility: offer.visibility,
        })),
      },
      contacts: {
        create: input.contacts.map((contact) => ({
          name: contact.name,
          role: contact.role ?? undefined,
          email: contact.email ?? undefined,
          phone: contact.phone ?? undefined,
          privacyLevel: contact.privacyLevel ?? "PRIVATE",
        })),
      },
    },
  });

  await triggerGraphRecompute(user.orgId);

  await prisma.auditLog.create({
    data: {
      orgId: user.orgId,
      actorId: user.id,
      entity: "Company",
      entityId: company.id,
      action: "CREATE",
      after: input,
    },
  });

  revalidatePath("/dashboard");
  revalidatePath(`/companies/${company.id}`);

  return { id: company.id };
}
