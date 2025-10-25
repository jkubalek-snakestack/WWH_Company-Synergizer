-- Row Level Security and visibility policies for the WWH Company Synergizer
-- This file is safe to re-run; policies are recreated each time.

CREATE SCHEMA IF NOT EXISTS auth;

-- Resolve the caller org id from Supabase JWT or session settings
CREATE OR REPLACE FUNCTION auth.current_org_id()
RETURNS text
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  claims jsonb;
  org_id_text text;
BEGIN
  org_id_text := NULL;

  BEGIN
    claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
  EXCEPTION
    WHEN others THEN
      claims := NULL;
  END;

  IF claims ? 'org_id' THEN
    org_id_text := claims ->> 'org_id';
  END IF;

  IF org_id_text IS NULL THEN
    BEGIN
      org_id_text := nullif(current_setting('app.current_org_id', true), '');
    EXCEPTION
      WHEN others THEN
        org_id_text := NULL;
    END;
  END IF;

  RETURN org_id_text;
END;
$$;

-- Helper to read the caller's company memberships from JWT claims
CREATE OR REPLACE FUNCTION auth.current_company_ids()
RETURNS text[]
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  claims jsonb;
  ids text[];
BEGIN
  ids := ARRAY[]::text[];

  BEGIN
    claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
  EXCEPTION
    WHEN others THEN
      claims := NULL;
  END;

  IF claims ? 'company_ids' THEN
    SELECT coalesce(array_agg(value), ARRAY[]::text[]) INTO ids
    FROM jsonb_array_elements_text(claims -> 'company_ids') AS value;
  ELSIF claims ? 'company_id' THEN
    ids := ARRAY[claims ->> 'company_id'];
  END IF;

  RETURN coalesce(ids, ARRAY[]::text[]);
END;
$$;

-- Does the caller belong to the provided company?
CREATE OR REPLACE FUNCTION auth.has_company_membership(target_company_id text)
RETURNS boolean
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  memberships text[];
BEGIN
  memberships := auth.current_company_ids();
  RETURN target_company_id = ANY(memberships);
END;
$$;

-- Determine if the caller's org is marked as a partner of the owner org.
-- Expects an OrgPartnerAccess(ownerOrgId, partnerOrgId) join table populated by application logic.
CREATE OR REPLACE FUNCTION auth.has_partner_access(owner_org_id text)
RETURNS boolean
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  current_org text := auth.current_org_id();
  permitted boolean := FALSE;
BEGIN
  IF current_org IS NULL THEN
    RETURN FALSE;
  END IF;

  IF owner_org_id = current_org THEN
    RETURN TRUE;
  END IF;

  IF to_regclass('public."OrgPartnerAccess"') IS NULL THEN
    RETURN FALSE;
  END IF;

  SELECT EXISTS (
    SELECT 1
    FROM "OrgPartnerAccess"
    WHERE "ownerOrgId" = owner_org_id
      AND "partnerOrgId" = current_org
  )
  INTO permitted;

  RETURN permitted;
END;
$$;

-- Centralised visibility check used by companies, needs, offers, and contacts
CREATE OR REPLACE FUNCTION auth.can_access_company_item(owner_org_id text, company_id text, visibility "Visibility")
RETURNS boolean
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  current_org text := auth.current_org_id();
BEGIN
  IF current_org IS NULL THEN
    RETURN FALSE;
  END IF;

  IF owner_org_id = current_org THEN
    IF visibility = 'PRIVATE' THEN
      RETURN auth.has_company_membership(company_id);
    ELSE
      RETURN TRUE;
    END IF;
  END IF;

  IF visibility = 'PARTNER' THEN
    RETURN auth.has_partner_access(owner_org_id);
  END IF;

  RETURN FALSE;
END;
$$;

-- Organisations ------------------------------------------------------------
ALTER TABLE "Org" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Org" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "org_isolation_select" ON "Org";
DROP POLICY IF EXISTS "org_select_self" ON "Org";
CREATE POLICY "org_select_self" ON "Org"
  FOR SELECT
  USING ("id" = auth.current_org_id());
DROP POLICY IF EXISTS "org_isolation_write" ON "Org";
DROP POLICY IF EXISTS "org_write_self" ON "Org";
CREATE POLICY "org_write_self" ON "Org"
  USING ("id" = auth.current_org_id())
  WITH CHECK ("id" = auth.current_org_id());

-- Users -------------------------------------------------------------------
ALTER TABLE "User" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "User" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "user_tenant_access" ON "User";
DROP POLICY IF EXISTS "user_same_org" ON "User";
CREATE POLICY "user_same_org" ON "User"
  USING ("orgId" = auth.current_org_id())
  WITH CHECK ("orgId" = auth.current_org_id());

-- Capability tags ---------------------------------------------------------
ALTER TABLE "CapabilityTag" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "CapabilityTag" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "capability_tag_tenant_access" ON "CapabilityTag";
DROP POLICY IF EXISTS "capability_tag_same_org" ON "CapabilityTag";
CREATE POLICY "capability_tag_same_org" ON "CapabilityTag"
  USING ("orgId" = auth.current_org_id())
  WITH CHECK ("orgId" = auth.current_org_id());

-- Companies ---------------------------------------------------------------
ALTER TABLE "Company" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Company" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "company_tenant_write" ON "Company";
DROP POLICY IF EXISTS "company_write_tenant" ON "Company";
CREATE POLICY "company_write_tenant" ON "Company"
  USING ("orgId" = auth.current_org_id())
  WITH CHECK ("orgId" = auth.current_org_id());
DROP POLICY IF EXISTS "company_select_visibility" ON "Company";
CREATE POLICY "company_select_visibility" ON "Company"
  FOR SELECT
  USING (
    auth.can_access_company_item("orgId", "id", "visibility")
  );

-- Needs -------------------------------------------------------------------
ALTER TABLE "Need" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Need" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "need_write_tenant" ON "Need";
CREATE POLICY "need_write_tenant" ON "Need"
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Need"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Need"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  );
DROP POLICY IF EXISTS "need_select_visibility" ON "Need";
CREATE POLICY "need_select_visibility" ON "Need"
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Need"."companyId"
        AND auth.can_access_company_item("Company"."orgId", "Company"."id", "Need"."visibility")
    )
  );

-- Offers ------------------------------------------------------------------
ALTER TABLE "Offer" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Offer" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "offer_write_tenant" ON "Offer";
CREATE POLICY "offer_write_tenant" ON "Offer"
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Offer"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Offer"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  );
DROP POLICY IF EXISTS "offer_select_visibility" ON "Offer";
CREATE POLICY "offer_select_visibility" ON "Offer"
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Offer"."companyId"
        AND auth.can_access_company_item("Company"."orgId", "Company"."id", "Offer"."visibility")
    )
  );

-- Contacts ----------------------------------------------------------------
ALTER TABLE "Contact" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Contact" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "contact_write_tenant" ON "Contact";
CREATE POLICY "contact_write_tenant" ON "Contact"
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Contact"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Contact"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  );
DROP POLICY IF EXISTS "contact_select_visibility" ON "Contact";
CREATE POLICY "contact_select_visibility" ON "Contact"
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "Contact"."companyId"
        AND auth.can_access_company_item("Company"."orgId", "Company"."id", "Contact"."privacyLevel")
    )
  );

-- Company Tag joins -------------------------------------------------------
ALTER TABLE "CompanyTag" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "CompanyTag" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "company_tag_write" ON "CompanyTag";
CREATE POLICY "company_tag_write" ON "CompanyTag"
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "CompanyTag"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "CompanyTag"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  );
DROP POLICY IF EXISTS "company_tag_select" ON "CompanyTag";
CREATE POLICY "company_tag_select" ON "CompanyTag"
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM "Company"
      WHERE "Company"."id" = "CompanyTag"."companyId"
        AND "Company"."orgId" = auth.current_org_id()
    )
  );

-- Opportunities -----------------------------------------------------------
ALTER TABLE "Opportunity" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Opportunity" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "opportunity_tenant_access" ON "Opportunity";
CREATE POLICY "opportunity_tenant_access" ON "Opportunity"
  USING ("orgId" = auth.current_org_id())
  WITH CHECK ("orgId" = auth.current_org_id());

-- Playbooks ---------------------------------------------------------------
ALTER TABLE "Playbook" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Playbook" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "playbook_tenant" ON "Playbook";
CREATE POLICY "playbook_tenant" ON "Playbook"
  USING (
    EXISTS (
      SELECT 1 FROM "Opportunity"
      WHERE "Opportunity"."id" = "Playbook"."opportunityId"
        AND "Opportunity"."orgId" = auth.current_org_id()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "Opportunity"
      WHERE "Opportunity"."id" = "Playbook"."opportunityId"
        AND "Opportunity"."orgId" = auth.current_org_id()
    )
  );

-- Audit logs --------------------------------------------------------------
ALTER TABLE "AuditLog" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "AuditLog" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "audit_log_select" ON "AuditLog";
DROP POLICY IF EXISTS "audit_log_tenant_write" ON "AuditLog";
DROP POLICY IF EXISTS "audit_log_write" ON "AuditLog";
CREATE POLICY "audit_log_select" ON "AuditLog"
  FOR SELECT
  USING ("orgId" = auth.current_org_id());
CREATE POLICY "audit_log_write" ON "AuditLog"
  USING ("orgId" = auth.current_org_id())
  WITH CHECK ("orgId" = auth.current_org_id());

-- Partner access join table -----------------------------------------------
DO $$
BEGIN
  IF to_regclass('public."OrgPartnerAccess"') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE "OrgPartnerAccess" ENABLE ROW LEVEL SECURITY';
    EXECUTE 'ALTER TABLE "OrgPartnerAccess" FORCE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS "org_partner_select" ON "OrgPartnerAccess"';
    EXECUTE 'CREATE POLICY "org_partner_select" ON "OrgPartnerAccess" FOR SELECT USING (("ownerOrgId" = auth.current_org_id()) OR ("partnerOrgId" = auth.current_org_id()))';
    EXECUTE 'DROP POLICY IF EXISTS "org_partner_write" ON "OrgPartnerAccess"';
    EXECUTE 'CREATE POLICY "org_partner_write" ON "OrgPartnerAccess" USING ("ownerOrgId" = auth.current_org_id()) WITH CHECK ("ownerOrgId" = auth.current_org_id())';
  END IF;
END;
$$;

-- -------------------------------------------------------------------------
-- Verification helper queries (run after applying the policies):
--
-- 1. Assume :org_id owns company :company_private and :company_public, with
--    OrgPartnerAccess rows granting partner_org access.
--
--    SET LOCAL request.jwt.claims = jsonb_build_object(
--      'org_id', :org_id,
--      'company_ids', jsonb_build_array(:company_private)
--    );
--    SELECT id, visibility FROM "Company" ORDER BY visibility;
--      → returns all companies in the org, including PRIVATE belonging to :company_private.
--
-- 2. Partner org access to PARTNER rows:
--    SET LOCAL request.jwt.claims = jsonb_build_object('org_id', :partner_org);
--    SELECT id FROM "Need" WHERE visibility = 'PARTNER';
--      → returns rows when OrgPartnerAccess(ownerOrgId = :org_id, partnerOrgId = :partner_org) exists.
--
-- 3. Partner org denied for PRIVATE rows:
--    SET LOCAL request.jwt.claims = jsonb_build_object('org_id', :partner_org);
--    SELECT id FROM "Offer" WHERE visibility = 'PRIVATE';
--      → returns zero rows.
--
-- 4. User without company membership cannot see PRIVATE contact:
--    SET LOCAL request.jwt.claims = jsonb_build_object('org_id', :org_id);
--    SELECT id FROM "Contact" WHERE "privacyLevel" = 'PRIVATE';
--      → returns zero rows.
