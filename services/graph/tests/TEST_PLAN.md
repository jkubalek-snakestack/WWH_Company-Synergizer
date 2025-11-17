# WWH Company Synergizer - Test Plan

## Test Plan Overview

This document outlines the comprehensive test plan based on risk analysis. Tests are organized by component with priority levels (High/Medium/Low) and target file locations.

---

## Test Groups

| Test Group | File Location | Priority Focus |
|------------|---------------|----------------|
| Models | `tests/test_models.py` | High - Core data validation |
| Graph/Storage | `tests/test_storage.py` | High - Data integrity |
| API | `tests/test_api.py` (extend) | High - Error handling |
| CLI | `tests/test_cli.py` | Medium - User workflows |
| Narrative Parser | `tests/test_narrative.py` (extend) | Medium - LLM integration |
| Analysis Engine | `tests/test_analysis.py` (extend) | Medium - Business logic |

---

## Detailed Test Cases

### 1. Models Tests (`tests/test_models.py`)

| Test Case | Priority | Description | Risk Addressed |
|-----------|----------|-------------|----------------|
| `test_company_profile_requires_slug` | **High** | Verify `CompanyProfile.from_dict()` raises error when `slug` is missing | Missing validation for required fields |
| `test_company_profile_requires_name` | **High** | Verify `CompanyProfile.from_dict()` raises error when `name` is missing | Missing validation for required fields |
| `test_company_profile_handles_optional_fields` | Medium | Verify all optional fields default correctly when missing | Data integrity |
| `test_company_profile_validates_nested_objects` | Medium | Verify nested objects (Location, Capability, Need) parse correctly | Nested validation |
| `test_capability_from_dict_with_invalid_channels` | **High** | Verify invalid engagement channels are handled gracefully | EngagementChannel enum fragility |
| `test_need_from_dict_with_invalid_channels` | **High** | Verify invalid engagement channels in needs are handled | EngagementChannel enum fragility |
| `test_engagement_channel_from_value_valid` | Medium | Test `EngagementChannel.from_value()` with valid values | Enum handling |
| `test_engagement_channel_from_value_invalid` | **High** | Test `EngagementChannel.from_value()` with invalid values | Enum error handling |
| `test_location_from_dict_none` | Low | Verify `Location.from_dict(None)` returns None | Null handling |
| `test_contact_from_dict_minimal` | Low | Verify Contact can be created with only name | Minimal data |
| `test_company_profile_vectorize_empty_fields` | Low | Verify `vectorize()` handles empty/None fields gracefully | Edge cases |
| `test_company_profile_plugin_points_plugs` | Low | Verify `plugin_points()` and `plugs()` return correct lists | Method correctness |

---

### 2. Graph/Storage Tests (`tests/test_storage.py`)

| Test Case | Priority | Description | Risk Addressed |
|-----------|----------|-------------|----------------|
| `test_graph_upsert_company_basic` | Medium | Verify basic company insertion works | Core functionality |
| `test_graph_upsert_company_generates_slug` | Medium | Verify slug is auto-generated when missing | Slug generation |
| `test_graph_upsert_company_duplicate_slug` | **High** | Verify duplicate slugs overwrite existing company (or raise error) | Duplicate slug handling |
| `test_graph_company_raises_keyerror_missing` | **High** | Verify `company()` raises KeyError for non-existent slug | Missing company handling |
| `test_graph_remove_company_removes_edges` | Medium | Verify removing company also removes all edges | Graph integrity |
| `test_graph_link_companies_valid` | Medium | Verify linking companies with valid slugs works | Link validation |
| `test_graph_link_companies_invalid_source` | **High** | Verify linking with invalid source slug raises error | Link validation |
| `test_graph_link_companies_invalid_target` | **High** | Verify linking with invalid target slug raises error | Link validation |
| `test_graph_matches_for_returns_correct_matches` | Medium | Verify `matches_for()` returns correct matches | Query correctness |
| `test_graph_matches_for_empty_returns_empty` | Low | Verify `matches_for()` returns empty list for company with no matches | Edge cases |
| `test_graph_adjacency_matrix_correctness` | Low | Verify adjacency matrix structure is correct | Data structure |
| `test_graph_ingest_multiple_companies` | Medium | Verify `ingest()` correctly adds multiple companies | Bulk operations |
| `test_graph_edges_iterator` | Low | Verify `edges()` iterator works correctly | Iterator correctness |

---

### 3. API Tests (`tests/test_api.py` - extend existing)

| Test Case | Priority | Description | Risk Addressed |
|-----------|----------|-------------|----------------|
| `test_analyze_returns_opportunities_and_matches` | Medium | ✅ EXISTS - Verify successful analysis returns data | Core functionality |
| `test_analyze_requires_profiles` | Medium | ✅ EXISTS - Verify empty profiles returns 400 | Input validation |
| `test_analyze_handles_missing_slug` | **High** | Verify API returns 400/422 when profile missing `slug` | Missing validation |
| `test_analyze_handles_missing_name` | **High** | Verify API returns 400/422 when profile missing `name` | Missing validation |
| `test_analyze_handles_invalid_json_structure` | **High** | Verify API handles malformed profile data gracefully | Error handling |
| `test_analyze_handles_invalid_engagement_channels` | **High** | Verify API handles invalid channel values in profiles | Enum validation |
| `test_analyze_with_template_bundle` | Medium | Verify template bundle processing works | Template integration |
| `test_analyze_with_invalid_template_bundle` | Medium | Verify invalid template bundle is handled gracefully | Template error handling |
| `test_analyze_response_structure` | Medium | Verify response contains all expected fields | Response validation |
| `test_analyze_empty_opportunities_allowed` | Low | Verify API returns 200 even when no opportunities found | Edge cases |
| `test_analyze_large_dataset_performance` | Low | Verify API handles large number of companies reasonably | Performance |
| `test_analyze_profiles_alias_works` | Low | Verify `companies` alias works same as `profiles` | API compatibility |
| `test_analyze_extra_fields_ignored` | Low | Verify extra fields in request are ignored (extra="ignore") | Input sanitization |

---

### 4. CLI Tests (`tests/test_cli.py` - new file)

| Test Case | Priority | Description | Risk Addressed |
|-----------|----------|-------------|----------------|
| `test_cli_load_profiles_valid_json` | Medium | Verify loading valid JSON file works | File handling |
| `test_cli_load_profiles_missing_file` | **High** | Verify missing file raises appropriate error | File handling |
| `test_cli_load_profiles_invalid_json` | **High** | Verify invalid JSON raises appropriate error | JSON validation |
| `test_cli_load_profiles_malformed_structure` | **High** | Verify malformed JSON structure (missing "companies" key) handled | JSON validation |
| `test_cli_build_engine_with_templates` | Medium | Verify engine builds correctly with templates | Template integration |
| `test_cli_build_engine_missing_template_file` | Medium | Verify missing template file is handled | Template error handling |
| `test_cli_build_engine_invalid_template_file` | Medium | Verify invalid template JSON is handled | Template validation |
| `test_cli_main_writes_report_file` | Low | Verify report file is written when `--report` specified | Output handling |
| `test_cli_main_prints_to_console` | Low | Verify output prints to console when no `--report` | Output handling |
| `test_cli_narrative_requires_model` | Medium | Verify `--narrative` requires `--openai-model` | CLI validation |
| `test_cli_narrative_missing_file` | Medium | Verify missing narrative file is handled | File handling |
| `test_cli_narrative_integration` | Low | Verify narrative parsing integrates with CLI workflow | Integration |

---

### 5. Narrative Parser Tests (`tests/test_narrative.py` - extend existing)

| Test Case | Priority | Description | Risk Addressed |
|-----------|----------|-------------|----------------|
| `test_parser_builds_profile_from_json_payload` | Medium | ✅ EXISTS - Verify basic parsing works | Core functionality |
| `test_parser_generates_slug_when_missing` | Medium | ✅ EXISTS - Verify slug generation | Slug generation |
| `test_parser_extracts_json_from_wrapped_response` | Medium | ✅ EXISTS - Verify JSON extraction from prose | JSON extraction |
| `test_parser_extract_json_malformed_json` | **High** | Verify malformed JSON in response is handled | JSON extraction fragility |
| `test_parser_extract_json_no_json_found` | **High** | Verify error when no JSON found in response | JSON extraction error handling |
| `test_parser_extract_json_nested_structures` | Medium | Verify nested JSON structures are extracted correctly | JSON extraction edge cases |
| `test_parser_slugify_special_characters` | Low | Verify slug generation handles special characters | Slug generation edge cases |
| `test_parser_slugify_empty_name` | **High** | Verify empty name generates valid slug (fallback to UUID) | Slug generation edge cases |
| `test_parser_default_name_fallback` | Medium | Verify "Unnamed Organization" used when name missing | Default handling |
| `test_parser_openai_model_missing_package` | Medium | Verify clear error when openai package not installed | Dependency handling |
| `test_parser_openai_model_api_error` | Low | Verify API errors are handled gracefully | External API errors |
| `test_prompt_builder_includes_guidance` | Low | ✅ EXISTS - Verify prompt includes schema | Prompt validation |

---

### 6. Analysis Engine Tests (`tests/test_analysis.py` - extend existing)

| Test Case | Priority | Description | Risk Addressed |
|-----------|----------|-------------|----------------|
| `test_engine_generates_opportunities` | Medium | ✅ EXISTS - Verify opportunities are generated | Core functionality |
| `test_high_priority_opportunities_present` | Medium | ✅ EXISTS - Verify priority assignment works | Priority logic |
| `test_engine_find_complementary_pairs_empty` | Low | Verify empty result when no companies match | Edge cases |
| `test_engine_find_complementary_pairs_single_company` | Low | Verify no matches for single company | Edge cases |
| `test_engine_build_opportunities_no_matches` | Low | Verify empty opportunities list when no matches | Edge cases |
| `test_engine_register_companies_duplicate_slugs` | **High** | Verify duplicate slugs are handled (overwrite or error) | Duplicate handling |
| `test_engine_profile_missing_company` | **High** | Verify `profile()` raises error for missing slug | Missing company handling |
| `test_engine_term_indexing` | Low | Verify term index is built correctly | Internal state |
| `test_engine_triad_generation_requires_two_pairs` | Medium | Verify triads only generated when 2+ pairs exist | Triad logic |
| `test_engine_priority_scoring` | Low | Verify priority scoring function works correctly | Priority logic |
| `test_engine_expected_outcomes_generation` | Low | Verify expected outcomes are generated appropriately | Outcome logic |
| `test_engine_large_dataset_performance` | Low | Verify performance with 50+ companies is acceptable | Performance |

---

### 7. Template Library Tests (`tests/test_templates.py` - new file)

| Test Case | Priority | Description | Risk Addressed |
|-----------|----------|-------------|----------------|
| `test_template_library_load_from_file` | Medium | Verify loading templates from JSON file works | File loading |
| `test_template_library_load_from_dict` | Medium | Verify loading templates from dict works | Dict loading |
| `test_template_library_template_missing_raises` | **High** | Verify `template()` raises KeyError for missing template | Missing template handling |
| `test_template_library_tier_missing_raises` | **High** | Verify `tier()` raises KeyError for missing tier | Missing tier handling |
| `test_template_library_auto_complete_profile` | Medium | Verify profile auto-completion fills required fields | Template application |
| `test_template_library_group_companies` | Medium | Verify company grouping by tiering rules works | Tiering logic |
| `test_template_library_group_companies_no_matches` | Low | Verify grouping returns empty buckets when no matches | Edge cases |
| `test_tiering_rule_applies_to_company` | Medium | Verify tiering rule matching logic works | Rule matching |
| `test_tiering_rule_case_insensitive` | Low | Verify tiering rules are case-insensitive | Rule matching edge cases |

---

## Test Execution Priority

### Phase 1: Critical Path (High Priority)
Focus on tests that prevent crashes and data corruption:
- All **High** priority tests in Models, Graph/Storage, and API
- These address the most critical bugs identified

### Phase 2: Core Functionality (Medium Priority)
Ensure all user-facing features work correctly:
- Medium priority tests across all groups
- Integration between components

### Phase 3: Edge Cases & Polish (Low Priority)
Cover edge cases and improve robustness:
- Low priority tests
- Performance and optimization tests

---

## Test File Structure

```
services/graph/tests/
├── test_models.py          (new - models validation)
├── test_storage.py          (new - graph operations)
├── test_api.py             (extend - add error cases)
├── test_cli.py             (new - CLI workflows)
├── test_narrative.py       (extend - add error cases)
├── test_analysis.py        (extend - add edge cases)
├── test_templates.py       (new - template library)
└── conftest.py            (new - shared fixtures)
```

---

## Notes

- **High Priority** tests address critical bugs that could cause crashes or data loss
- **Medium Priority** tests ensure core functionality works as expected
- **Low Priority** tests improve robustness and catch edge cases
- Tests marked with ✅ already exist and may need extension
- Consider using `pytest.fixture` for shared test data (sample profiles, etc.)
- Use `pytest.parametrize` for testing multiple similar cases
- Mock external dependencies (OpenAI API) in narrative parser tests

