import { PrismaClient, Visibility, Urgency, Capacity, OpportunityStatus, Prisma } from '@prisma/client';

const prisma = new PrismaClient();

async function clearDatabase() {
  await prisma.playbook.deleteMany();
  await prisma.opportunity.deleteMany();
  await prisma.contact.deleteMany();
  await prisma.offer.deleteMany();
  await prisma.need.deleteMany();
  await prisma.companyTag.deleteMany();
  await prisma.capabilityTag.deleteMany();
  await prisma.company.deleteMany();
  await prisma.auditLog.deleteMany();
  await prisma.user.deleteMany();
  await prisma.org.deleteMany();
}

async function seed() {
  await clearDatabase();

  const [wwh, snake, giv] = await Promise.all([
    prisma.org.create({ data: { name: 'WWH Alliance' } }),
    prisma.org.create({ data: { name: 'Snake Stack Games' } }),
    prisma.org.create({ data: { name: 'Global Impact Ventures' } }),
  ]);

  const [wwhAdmin, snakeLead, givCoordinator] = await Promise.all([
    prisma.user.create({
      data: {
        orgId: wwh.id,
        email: 'ops@wwh.example',
        role: 'org_admin',
      },
    }),
    prisma.user.create({
      data: {
        orgId: snake.id,
        email: 'hello@snakestack.example',
        role: 'member',
      },
    }),
    prisma.user.create({
      data: {
        orgId: giv.id,
        email: 'field@giv.example',
        role: 'facilitator',
      },
    }),
  ]);

  const [waterInfra, microgrid, education, gameDesign, storytelling, logistics, training] = await Promise.all([
    prisma.capabilityTag.create({ data: { orgId: wwh.id, name: 'Water Infrastructure', slug: 'water-infrastructure' } }),
    prisma.capabilityTag.create({ data: { orgId: wwh.id, name: 'Microgrid Energy', slug: 'microgrid-energy' } }),
    prisma.capabilityTag.create({ data: { orgId: wwh.id, name: 'Education Enablement', slug: 'education-enablement' } }),
    prisma.capabilityTag.create({ data: { orgId: snake.id, name: 'Game Design', slug: 'game-design' } }),
    prisma.capabilityTag.create({ data: { orgId: snake.id, name: 'Storytelling', slug: 'storytelling' } }),
    prisma.capabilityTag.create({ data: { orgId: giv.id, name: 'Field Logistics', slug: 'field-logistics' } }),
    prisma.capabilityTag.create({ data: { orgId: giv.id, name: 'Community Training', slug: 'community-training' } }),
  ]);

  const aquaReach = await prisma.company.create({
    data: {
      orgId: wwh.id,
      name: 'AquaReach Foundation',
      region: 'Kigoma, Tanzania',
      mission: 'Deliver sustainable water systems to remote villages.',
      wwhKeys: ['Water Stewardship', 'Community Elevation'],
      visibility: Visibility.PUBLIC,
    },
  });

  const gridWise = await prisma.company.create({
    data: {
      orgId: wwh.id,
      name: 'GridWise IT',
      region: 'Austin, USA',
      mission: 'Optimize energy distribution with adaptive microgrids.',
      wwhKeys: ['Energy Synergy', 'Innovation'],
      visibility: Visibility.PARTNER,
    },
  });

  const snakeStudios = await prisma.company.create({
    data: {
      orgId: snake.id,
      name: 'Snake Stack Studios',
      region: 'Seattle, USA',
      mission: 'Create playful experiences that inspire social impact.',
      wwhKeys: ['Creative Spark', 'Story Worlds'],
      visibility: Visibility.PUBLIC,
    },
  });

  const playForge = await prisma.company.create({
    data: {
      orgId: snake.id,
      name: 'PlayForge Labs',
      region: 'Portland, USA',
      mission: 'Blend physical and digital learning adventures.',
      wwhKeys: ['Learning Engagement', 'Systems Thinking'],
      visibility: Visibility.PARTNER,
    },
  });

  const villageEducators = await prisma.company.create({
    data: {
      orgId: giv.id,
      name: 'Village Educators Collective',
      region: 'Northern Uganda',
      mission: 'Equip local facilitators with modern curriculum tools.',
      wwhKeys: ['Education', 'Community Elevation'],
      visibility: Visibility.PUBLIC,
    },
  });

  const terraFlow = await prisma.company.create({
    data: {
      orgId: giv.id,
      name: 'TerraFlow Logistics',
      region: 'Nairobi, Kenya',
      mission: 'Provide last-mile logistics for humanitarian deployments.',
      wwhKeys: ['Infrastructure', 'Rapid Response'],
      visibility: Visibility.PARTNER,
    },
  });

  await Promise.all([
    prisma.companyTag.createMany({
      data: [
        { companyId: aquaReach.id, tagId: waterInfra.id },
        { companyId: aquaReach.id, tagId: education.id },
        { companyId: gridWise.id, tagId: microgrid.id },
        { companyId: snakeStudios.id, tagId: gameDesign.id },
        { companyId: snakeStudios.id, tagId: storytelling.id },
        { companyId: playForge.id, tagId: storytelling.id },
        { companyId: villageEducators.id, tagId: training.id },
        { companyId: terraFlow.id, tagId: logistics.id },
      ],
    }),
    prisma.need.createMany({
      data: [
        {
          companyId: aquaReach.id,
          title: 'Solar pump stabilization',
          description: 'Need dependable power storage for night operations.',
          tags: ['water', 'energy'],
          urgency: Urgency.HIGH,
          visibility: Visibility.PARTNER,
        },
        {
          companyId: gridWise.id,
          title: 'Field deployment partner',
          description: 'Seeking rural operators for microgrid pilot installs.',
          tags: ['deployment', 'africa'],
          urgency: Urgency.MED,
          visibility: Visibility.PARTNER,
        },
        {
          companyId: villageEducators.id,
          title: 'STEM learning games',
          description: 'Curriculum-aligned games that work offline.',
          tags: ['education', 'games'],
          urgency: Urgency.MED,
          visibility: Visibility.PUBLIC,
        },
        {
          companyId: terraFlow.id,
          title: 'Cold chain sensors',
          description: 'Low-cost monitoring devices for vaccine routes.',
          tags: ['logistics', 'health'],
          urgency: Urgency.HIGH,
          visibility: Visibility.PRIVATE,
        },
      ],
    }),
    prisma.offer.createMany({
      data: [
        {
          companyId: gridWise.id,
          title: 'Microgrid analytics platform',
          description: 'Telemetry and optimization with remote tuning.',
          tags: ['energy', 'software'],
          capacity: Capacity.MED,
          visibility: Visibility.PARTNER,
        },
        {
          companyId: aquaReach.id,
          title: 'Community liaison network',
          description: 'Trusted community stewards in 40+ villages.',
          tags: ['community', 'africa'],
          capacity: Capacity.HIGH,
          visibility: Visibility.PUBLIC,
        },
        {
          companyId: snakeStudios.id,
          title: 'Narrative design sprint',
          description: 'Two-week collaborative workshop for story-led engagement.',
          tags: ['storytelling', 'design'],
          capacity: Capacity.MED,
          visibility: Visibility.PARTNER,
        },
        {
          companyId: playForge.id,
          title: 'Offline learning kits',
          description: 'Card and board games aligned to literacy milestones.',
          tags: ['education', 'games'],
          capacity: Capacity.LOW,
          visibility: Visibility.PUBLIC,
        },
        {
          companyId: terraFlow.id,
          title: 'Regional logistics operations',
          description: 'Fleet management and customs navigation.',
          tags: ['logistics', 'operations'],
          capacity: Capacity.MED,
          visibility: Visibility.PARTNER,
        },
      ],
    }),
    prisma.contact.createMany({
      data: [
        {
          companyId: aquaReach.id,
          name: 'Nuru Amani',
          role: 'Program Director',
          email: 'nuru@aquareach.example',
          privacyLevel: Visibility.PARTNER,
        },
        {
          companyId: gridWise.id,
          name: 'Lamar Steele',
          role: 'CEO',
          email: 'lamar@gridwise.example',
          privacyLevel: Visibility.PRIVATE,
        },
        {
          companyId: snakeStudios.id,
          name: 'Aria Bowen',
          role: 'Creative Director',
          email: 'aria@snakestudios.example',
          privacyLevel: Visibility.PARTNER,
        },
        {
          companyId: villageEducators.id,
          name: 'Joel Okello',
          role: 'Training Lead',
          email: 'joel@vec.example',
          privacyLevel: Visibility.PUBLIC,
        },
      ],
    }),
  ]);

  const aquaNeed = await prisma.need.findFirstOrThrow({
    where: { companyId: aquaReach.id, title: 'Solar pump stabilization' },
  });
  const gridOffer = await prisma.offer.findFirstOrThrow({
    where: { companyId: gridWise.id, title: 'Microgrid analytics platform' },
  });
  const vecNeed = await prisma.need.findFirstOrThrow({
    where: { companyId: villageEducators.id, title: 'STEM learning games' },
  });
  const playForgeOffer = await prisma.offer.findFirstOrThrow({
    where: { companyId: playForge.id, title: 'Offline learning kits' },
  });

  const energyBridge = await prisma.opportunity.create({
    data: {
      orgId: wwh.id,
      sourceId: gridWise.id,
      targetId: aquaReach.id,
      needId: aquaNeed.id,
      offerId: gridOffer.id,
      score: 0.82,
      impact: 0.91,
      confidence: 0.76,
      breakdown: {
        alignment: 'Energy reliability for village water systems',
        resources: ['Analytics platform', 'Solar storage partners'],
        risks: ['Customs delays', 'Training capacity'],
      } satisfies Prisma.JsonObject,
      status: OpportunityStatus.IN_PROGRESS,
    },
  });

  const learningExchange = await prisma.opportunity.create({
    data: {
      orgId: snake.id,
      sourceId: playForge.id,
      targetId: villageEducators.id,
      needId: vecNeed.id,
      offerId: playForgeOffer.id,
      score: 0.74,
      impact: 0.68,
      confidence: 0.71,
      breakdown: {
        alignment: 'Offline literacy kits to extend training sessions',
        resources: ['Game designers', 'Local facilitators'],
        risks: ['Manufacturing lead time'],
      } satisfies Prisma.JsonObject,
      status: OpportunityStatus.OPEN,
    },
  });

  await prisma.playbook.createMany({
    data: [
      {
        opportunityId: energyBridge.id,
        version: 1,
        summary: 'Deploy microgrid boosters with AquaReach field teams.',
        sections: {
          steps: [
            'Confirm pilot villages',
            'Ship and install hybrid controllers',
            'Train pump stewards on analytics alerts',
          ],
          timeline: '6-week rollout',
          actors: ['GridWise engineers', 'AquaReach technicians'],
          risks: ['Weather access'],
          wwh_alignment: ['Water Stewardship', 'Energy Synergy'],
        } satisfies Prisma.JsonObject,
      },
      {
        opportunityId: learningExchange.id,
        version: 1,
        summary: 'Co-create offline STEM kits with Village Educators.',
        sections: {
          steps: ['Define curriculum goals', 'Prototype games', 'Train facilitators'],
          timeline: '8-week sprint',
          actors: ['PlayForge designers', 'Village Educators'],
          risks: ['Printing delays'],
          wwh_alignment: ['Creative Spark', 'Education'],
        } satisfies Prisma.JsonObject,
      },
    ],
  });

  await prisma.auditLog.createMany({
    data: [
      {
        orgId: wwh.id,
        actorId: wwhAdmin.id,
        entity: 'Opportunity',
        entityId: energyBridge.id,
        action: 'CREATE',
        after: { status: OpportunityStatus.IN_PROGRESS } satisfies Prisma.JsonValue,
      },
      {
        orgId: snake.id,
        actorId: snakeLead.id,
        entity: 'Playbook',
        entityId: learningExchange.id,
        action: 'INGEST',
        after: { version: 1 } satisfies Prisma.JsonValue,
      },
      {
        orgId: giv.id,
        actorId: givCoordinator.id,
        entity: 'Contact',
        action: 'CREATE',
        after: { name: 'Joel Okello' } satisfies Prisma.JsonValue,
      },
    ],
  });
}

seed()
  .then(() => {
    console.log('Database seeded successfully');
  })
  .catch((error) => {
    console.error('Seed failed', error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
