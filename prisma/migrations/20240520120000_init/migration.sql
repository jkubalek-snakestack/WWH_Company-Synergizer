-- Enable UUID generation for string ids cast from UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enumerations
CREATE TYPE "Visibility" AS ENUM ('PUBLIC', 'PARTNER', 'PRIVATE');
CREATE TYPE "Urgency" AS ENUM ('LOW', 'MED', 'HIGH');
CREATE TYPE "Capacity" AS ENUM ('LOW', 'MED', 'HIGH');
CREATE TYPE "OpportunityStatus" AS ENUM ('OPEN', 'ARCHIVED', 'IN_PROGRESS', 'WON', 'LOST');

-- Organizations
CREATE TABLE "Org" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users
CREATE TABLE "User" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "orgId" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "User_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Org"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "User_email_key" ON "User"("email");
CREATE INDEX "User_orgId_idx" ON "User"("orgId");

-- Capability tags
CREATE TABLE "CapabilityTag" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "orgId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    CONSTRAINT "CapabilityTag_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Org"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "CapabilityTag_slug_key" ON "CapabilityTag"("slug");
CREATE INDEX "CapabilityTag_orgId_idx" ON "CapabilityTag"("orgId");

-- Companies
CREATE TABLE "Company" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "orgId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "region" TEXT,
    "mission" TEXT,
    "wwhKeys" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    "visibility" "Visibility" NOT NULL DEFAULT 'PARTNER',
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "Company_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Org"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Company_orgId_idx" ON "Company"("orgId");
CREATE INDEX "Company_visibility_idx" ON "Company"("visibility");

-- Join table for company tags
CREATE TABLE "CompanyTag" (
    "companyId" TEXT NOT NULL,
    "tagId" TEXT NOT NULL,
    CONSTRAINT "CompanyTag_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "CompanyTag_tagId_fkey" FOREIGN KEY ("tagId") REFERENCES "CapabilityTag"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY ("companyId", "tagId")
);

CREATE INDEX "CompanyTag_tagId_idx" ON "CompanyTag"("tagId");

-- Needs
CREATE TABLE "Need" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "companyId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "tags" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    "urgency" "Urgency" NOT NULL DEFAULT 'MED',
    "visibility" "Visibility" NOT NULL DEFAULT 'PARTNER',
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "Need_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Need_companyId_idx" ON "Need"("companyId");
CREATE INDEX "Need_visibility_idx" ON "Need"("visibility");

-- Offers
CREATE TABLE "Offer" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "companyId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "tags" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    "capacity" "Capacity" NOT NULL DEFAULT 'MED',
    "visibility" "Visibility" NOT NULL DEFAULT 'PARTNER',
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "Offer_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Offer_companyId_idx" ON "Offer"("companyId");
CREATE INDEX "Offer_visibility_idx" ON "Offer"("visibility");

-- Contacts
CREATE TABLE "Contact" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "companyId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "role" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "privacyLevel" "Visibility" NOT NULL DEFAULT 'PRIVATE',
    CONSTRAINT "Contact_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Contact_companyId_idx" ON "Contact"("companyId");
CREATE INDEX "Contact_privacy_idx" ON "Contact"("privacyLevel");

-- Opportunities
CREATE TABLE "Opportunity" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "orgId" TEXT NOT NULL,
    "sourceId" TEXT NOT NULL,
    "targetId" TEXT NOT NULL,
    "needId" TEXT,
    "offerId" TEXT,
    "score" DOUBLE PRECISION NOT NULL,
    "impact" DOUBLE PRECISION NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "breakdown" JSONB NOT NULL,
    "status" "OpportunityStatus" NOT NULL DEFAULT 'OPEN',
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "Opportunity_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Org"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Opportunity_sourceId_fkey" FOREIGN KEY ("sourceId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Opportunity_targetId_fkey" FOREIGN KEY ("targetId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Opportunity_needId_fkey" FOREIGN KEY ("needId") REFERENCES "Need"("id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "Opportunity_offerId_fkey" FOREIGN KEY ("offerId") REFERENCES "Offer"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX "Opportunity_orgId_idx" ON "Opportunity"("orgId");
CREATE INDEX "Opportunity_sourceId_idx" ON "Opportunity"("sourceId");
CREATE INDEX "Opportunity_targetId_idx" ON "Opportunity"("targetId");
CREATE INDEX "Opportunity_status_idx" ON "Opportunity"("status");

-- Playbooks
CREATE TABLE "Playbook" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "opportunityId" TEXT NOT NULL,
    "version" INTEGER NOT NULL,
    "summary" TEXT NOT NULL,
    "sections" JSONB NOT NULL,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "Playbook_opportunityId_fkey" FOREIGN KEY ("opportunityId") REFERENCES "Opportunity"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Playbook_opportunityId_idx" ON "Playbook"("opportunityId");

-- Audit log
CREATE TABLE "AuditLog" (
    "id" TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "orgId" TEXT NOT NULL,
    "actorId" TEXT,
    "entity" TEXT NOT NULL,
    "entityId" TEXT,
    "action" TEXT NOT NULL,
    "before" JSONB,
    "after" JSONB,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "AuditLog_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Org"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "AuditLog_actorId_fkey" FOREIGN KEY ("actorId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX "AuditLog_orgId_idx" ON "AuditLog"("orgId");
CREATE INDEX "AuditLog_entity_idx" ON "AuditLog"("entity", "entityId");
