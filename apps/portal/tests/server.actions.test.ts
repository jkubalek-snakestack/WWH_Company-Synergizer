import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/utils", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/utils")>();
  return {
    ...actual,
    slugify: actual.slugify,
  };
});

const mockUser = { id: "user_1", orgId: "org_1" };
const mockCompanyRecord = {
  id: "comp_1",
  orgId: "org_1",
  name: "New Org",
  region: "NA",
  mission: "Testing",
  wwhKeys: ["Education"],
  visibility: "PARTNER",
  tags: [
    {
      tag: { id: "tag_1", name: "stem", slug: "stem" },
    },
  ],
  needs: [
    {
      id: "need_1",
      companyId: "comp_1",
      title: "Water",
      description: "Clean water",
      tags: ["water"],
      urgency: "HIGH",
      visibility: "PUBLIC",
    },
  ],
  offers: [
    {
      id: "offer_1",
      companyId: "comp_1",
      title: "Logistics Support",
      description: "Trucks",
      tags: ["logistics"],
      capacity: "MED",
      visibility: "PARTNER",
    },
  ],
  contacts: [
    {
      id: "contact_1",
      companyId: "comp_1",
      name: "Lee",
      role: "Coordinator",
      email: null,
      phone: null,
      privacyLevel: "PRIVATE",
    },
  ],
};

const companyCreate = vi.fn().mockResolvedValue({ id: "comp_1" });
const companyFindMany = vi.fn().mockResolvedValue([mockCompanyRecord]);
const auditCreate = vi.fn().mockResolvedValue({});
const opportunityUpdateMany = vi.fn().mockResolvedValue({ count: 1 });

vi.mock("../server/db/client", () => ({
  prisma: {
    company: {
      create: companyCreate,
      findMany: companyFindMany,
    },
    auditLog: {
      create: auditCreate,
    },
    opportunity: {
      updateMany: opportunityUpdateMany,
    },
  },
}));

const requireUser = vi.fn().mockResolvedValue(mockUser);
vi.mock("../server/auth", () => ({ requireUser }));

const revalidatePath = vi.fn();
vi.mock("next/cache", () => ({ revalidatePath }));

describe("server actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global as unknown as { fetch: typeof fetch }).fetch = vi
      .fn()
      .mockResolvedValue({ ok: true });
  });

  it("creates a company profile and triggers recompute", async () => {
    const { createCompanyAction } = await import("../server/actions/company");

    await createCompanyAction({
      company: {
        name: "New Org",
        region: "NA",
        mission: "Testing",
        wwhKeys: ["Education"],
        capabilities: ["STEM"],
      },
      needs: [
        {
          title: "Water",
          description: "Clean water",
          tags: ["Water"],
          urgency: "HIGH",
          visibility: "PUBLIC",
        },
      ],
      offers: [
        {
          title: "Logistics Support",
          description: "Trucks",
          tags: ["LOGISTICS"],
          capacity: "MED",
          visibility: "PARTNER",
        },
      ],
      contacts: [
        {
          name: "Lee",
          role: "Coordinator",
        },
      ],
    });

    expect(requireUser).toHaveBeenCalled();
    expect(companyCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        orgId: "org_1",
        name: "New Org",
      }),
    });
    expect(companyFindMany).toHaveBeenCalledWith({
      where: { orgId: "org_1" },
      include: expect.objectContaining({ needs: true, offers: true, contacts: true }),
    });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/recompute"),
      expect.objectContaining({ method: "POST" }),
    );
    expect(auditCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        entity: "Company",
        entityId: "comp_1",
        action: "CREATE",
      }),
    });
    expect(revalidatePath).toHaveBeenCalledWith("/dashboard");
  });

  it("updates opportunity status", async () => {
    const { updateOpportunityStatusAction } = await import(
      "../server/actions/opportunity"
    );

    await updateOpportunityStatusAction({
      opportunityId: "opp_1",
      companyId: "comp_1",
      status: "ARCHIVED",
    });

    expect(opportunityUpdateMany).toHaveBeenCalledWith({
      where: { id: "opp_1", orgId: "org_1" },
      data: { status: "ARCHIVED" },
    });
    expect(auditCreate).toHaveBeenCalledWith({
      data: expect.objectContaining({
        entity: "Opportunity",
        entityId: "opp_1",
        action: "UPDATE",
      }),
    });
    expect(revalidatePath).toHaveBeenCalledWith("/dashboard");
  });
});
