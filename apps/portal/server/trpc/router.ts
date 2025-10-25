import { OpportunityStatus } from "@prisma/client";
import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "./context";

const opportunityInclude = {
  need: {
    select: {
      id: true,
      title: true,
    },
  },
  offer: {
    select: {
      id: true,
      title: true,
    },
  },
  source: {
    select: {
      id: true,
      name: true,
    },
  },
  target: {
    select: {
      id: true,
      name: true,
    },
  },
};

export const appRouter = createTRPCRouter({
  dashboard: createTRPCRouter({
    overview: protectedProcedure.query(async ({ ctx }) => {
      const [companyCount, needCount, offerCount, opportunityCount, topOpportunities] =
        await Promise.all([
          ctx.prisma.company.count({ where: { orgId: ctx.user.orgId } }),
          ctx.prisma.need.count({ where: { company: { orgId: ctx.user.orgId } } }),
          ctx.prisma.offer.count({ where: { company: { orgId: ctx.user.orgId } } }),
          ctx.prisma.opportunity.count({ where: { orgId: ctx.user.orgId } }),
          ctx.prisma.opportunity.findMany({
            where: { orgId: ctx.user.orgId },
            orderBy: { score: "desc" },
            take: 10,
            include: opportunityInclude,
          }),
        ]);

      return {
        metrics: {
          companies: companyCount,
          needs: needCount,
          offers: offerCount,
          opportunities: opportunityCount,
        },
        topOpportunities: topOpportunities.map((opportunity) => ({
          ...opportunity,
          breakdown: opportunity.breakdown ?? {},
        })),
      };
    }),
  }),
  companies: createTRPCRouter({
    byId: protectedProcedure
      .input(z.object({ id: z.string().min(1) }))
      .query(async ({ ctx, input }) => {
        const company = await ctx.prisma.company.findFirst({
          where: { id: input.id, orgId: ctx.user.orgId },
          include: {
            needs: true,
            offers: true,
            contacts: true,
            tags: {
              include: {
                tag: true,
              },
            },
            sourceOpportunities: {
              where: { orgId: ctx.user.orgId },
              include: opportunityInclude,
            },
            targetOpportunities: {
              where: { orgId: ctx.user.orgId },
              include: opportunityInclude,
            },
          },
        });

        if (!company) {
          throw new Error("Company not found");
        }

        const capabilityNames = company.tags.map(({ tag }) => tag.name);
        const opportunities = [...company.sourceOpportunities, ...company.targetOpportunities]
          .sort((a, b) => b.score - a.score)
          .map((opportunity) => ({
            ...opportunity,
            breakdown: opportunity.breakdown ?? {},
          }));

        return {
          id: company.id,
          name: company.name,
          region: company.region,
          mission: company.mission,
          wwhKeys: company.wwhKeys,
          visibility: company.visibility,
          capabilities: capabilityNames,
          needs: company.needs,
          offers: company.offers,
          contacts: company.contacts,
          opportunities,
        };
      }),
    intakeOptions: protectedProcedure.query(async ({ ctx }) => {
      const capabilityTags = await ctx.prisma.capabilityTag.findMany({
        where: { orgId: ctx.user.orgId },
        orderBy: { name: "asc" },
      });

      return {
        capabilityTags: capabilityTags.map((tag) => ({ id: tag.id, name: tag.name })),
        wwhKeys: [
          "Education",
          "Health",
          "Community Dev",
          "Energy",
          "Finance",
          "Food/Water",
          "Logistics",
          "Housing",
          "Safety",
        ],
      };
    }),
  }),
  opportunities: createTRPCRouter({
    list: protectedProcedure
      .input(
        z
          .object({
            companyId: z.string().optional(),
            status: z.nativeEnum(OpportunityStatus).optional(),
            limit: z.number().int().positive().max(50).optional(),
          })
          .optional(),
      )
      .query(async ({ ctx, input }) => {
        const where = {
          orgId: ctx.user.orgId,
          ...(input?.companyId
            ? {
                OR: [{ sourceId: input.companyId }, { targetId: input.companyId }],
              }
            : {}),
          ...(input?.status ? { status: input.status } : {}),
        };

        const items = await ctx.prisma.opportunity.findMany({
          where,
          include: opportunityInclude,
          orderBy: { score: "desc" },
          take: input?.limit ?? undefined,
        });

        return items.map((opportunity) => ({
          ...opportunity,
          breakdown: opportunity.breakdown ?? {},
        }));
      }),
  }),
});

export type AppRouter = typeof appRouter;
