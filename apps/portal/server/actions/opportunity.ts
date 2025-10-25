"use server";

import { OpportunityStatus } from "@prisma/client";
import { revalidatePath } from "next/cache";
import { z } from "zod";

import { requireUser } from "../auth";
import { prisma } from "../db/client";

const updateSchema = z.object({
  opportunityId: z.string().min(1),
  status: z.nativeEnum(OpportunityStatus),
  companyId: z.string().min(1),
});

export type UpdateOpportunityInput = z.infer<typeof updateSchema>;

export async function updateOpportunityStatusAction(
  rawInput: UpdateOpportunityInput | FormData,
) {
  const user = await requireUser();
  const candidate =
    rawInput instanceof FormData
      ? {
          opportunityId: String(rawInput.get("opportunityId")),
          companyId: String(rawInput.get("companyId")),
          status: String(rawInput.get("status")),
        }
      : rawInput;
  const input = updateSchema.parse(candidate);

  const result = await prisma.opportunity.updateMany({
    where: { id: input.opportunityId, orgId: user.orgId },
    data: { status: input.status },
  });

  if (result.count === 0) {
    throw new Error("Opportunity not found");
  }

  await prisma.auditLog.create({
    data: {
      orgId: user.orgId,
      actorId: user.id,
      entity: "Opportunity",
      entityId: input.opportunityId,
      action: "UPDATE",
      after: { status: input.status },
    },
  });

  revalidatePath("/dashboard");
  revalidatePath(`/companies/${input.companyId}`);

  return { id: input.opportunityId, status: input.status };
}
