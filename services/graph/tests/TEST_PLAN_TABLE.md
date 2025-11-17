# Test Plan - Workable Table Format

## Quick Reference Table

| # | Test Group | Test File | Test Case Name | Priority | Risk Addressed |
|---|------------|-----------|----------------|----------|----------------|
| **MODELS** |
| 1 | Models | `test_models.py` | `test_company_profile_requires_slug` | **High** | Missing validation for required fields |
| 2 | Models | `test_models.py` | `test_company_profile_requires_name` | **High** | Missing validation for required fields |
| 3 | Models | `test_models.py` | `test_company_profile_handles_optional_fields` | Medium | Data integrity |
| 4 | Models | `test_models.py` | `test_company_profile_validates_nested_objects` | Medium | Nested validation |
| 5 | Models | `test_models.py` | `test_capability_from_dict_with_invalid_channels` | **High** | EngagementChannel enum fragility |
| 6 | Models | `test_models.py` | `test_need_from_dict_with_invalid_channels` | **High** | EngagementChannel enum fragility |
| 7 | Models | `test_models.py` | `test_engagement_channel_from_value_valid` | Medium | Enum handling |
| 8 | Models | `test_models.py` | `test_engagement_channel_from_value_invalid` | **High** | Enum error handling |
| 9 | Models | `test_models.py` | `test_location_from_dict_none` | Low | Null handling |
| 10 | Models | `test_models.py` | `test_contact_from_dict_minimal` | Low | Minimal data |
| 11 | Models | `test_models.py` | `test_company_profile_vectorize_empty_fields` | Low | Edge cases |
| 12 | Models | `test_models.py` | `test_company_profile_plugin_points_plugs` | Low | Method correctness |
| **GRAPH/STORAGE** |
| 13 | Graph/Storage | `test_storage.py` | `test_graph_upsert_company_basic` | Medium | Core functionality |
| 14 | Graph/Storage | `test_storage.py` | `test_graph_upsert_company_generates_slug` | Medium | Slug generation |
| 15 | Graph/Storage | `test_storage.py` | `test_graph_upsert_company_duplicate_slug` | **High** | ✅ IMPLEMENTED - Duplicate slug handling |
| 16 | Graph/Storage | `test_storage.py` | `test_graph_company_raises_keyerror_missing` | **High** | ✅ IMPLEMENTED - Missing company handling |
| 17 | Graph/Storage | `test_storage.py` | `test_graph_remove_company_removes_edges` | Medium | Graph integrity |
| 18 | Graph/Storage | `test_storage.py` | `test_graph_link_companies_valid` | Medium | Link validation |
| 19 | Graph/Storage | `test_storage.py` | `test_graph_link_companies_invalid_source` | **High** | ✅ IMPLEMENTED - Link validation |
| 20 | Graph/Storage | `test_storage.py` | `test_graph_link_companies_invalid_target` | **High** | ✅ IMPLEMENTED - Link validation |
| 21 | Graph/Storage | `test_storage.py` | `test_graph_matches_for_returns_correct_matches` | Medium | Query correctness |
| 22 | Graph/Storage | `test_storage.py` | `test_graph_matches_for_empty_returns_empty` | Low | Edge cases |
| 23 | Graph/Storage | `test_storage.py` | `test_graph_adjacency_matrix_correctness` | Low | Data structure |
| 24 | Graph/Storage | `test_storage.py` | `test_graph_ingest_multiple_companies` | Medium | Bulk operations |
| 25 | Graph/Storage | `test_storage.py` | `test_graph_edges_iterator` | Low | Iterator correctness |
| **API** |
| 26 | API | `test_api.py` | `test_analyze_returns_opportunities_and_matches` | Medium | ✅ EXISTS - Core functionality |
| 27 | API | `test_api.py` | `test_analyze_requires_profiles` | Medium | ✅ EXISTS - Input validation |
| 28 | API | `test_api.py` | `test_analyze_handles_missing_slug` | **High** | ✅ IMPLEMENTED - Missing validation |
| 29 | API | `test_api.py` | `test_analyze_handles_missing_name` | **High** | ✅ IMPLEMENTED - Missing validation |
| 30 | API | `test_api.py` | `test_analyze_handles_invalid_json_structure` | **High** | ✅ IMPLEMENTED - Error handling |
| 31 | API | `test_api.py` | `test_analyze_handles_invalid_engagement_channels` | **High** | ✅ IMPLEMENTED - Enum validation |
| 32 | API | `test_api.py` | `test_analyze_with_template_bundle` | Medium | Template integration |
| 33 | API | `test_api.py` | `test_analyze_with_invalid_template_bundle` | Medium | Template error handling |
| 34 | API | `test_api.py` | `test_analyze_response_structure` | Medium | Response validation |
| 35 | API | `test_api.py` | `test_analyze_empty_opportunities_allowed` | Low | Edge cases |
| 36 | API | `test_api.py` | `test_analyze_large_dataset_performance` | Low | Performance |
| 37 | API | `test_api.py` | `test_analyze_profiles_alias_works` | Low | API compatibility |
| 38 | API | `test_api.py` | `test_analyze_extra_fields_ignored` | Low | Input sanitization |
| **CLI** |
| 39 | CLI | `test_cli.py` | `test_cli_load_profiles_valid_json` | Medium | File handling |
| 40 | CLI | `test_cli.py` | `test_cli_load_profiles_missing_file` | **High** | File handling |
| 41 | CLI | `test_cli.py` | `test_cli_load_profiles_invalid_json` | **High** | JSON validation |
| 42 | CLI | `test_cli.py` | `test_cli_load_profiles_malformed_structure` | **High** | JSON validation |
| 43 | CLI | `test_cli.py` | `test_cli_build_engine_with_templates` | Medium | Template integration |
| 44 | CLI | `test_cli.py` | `test_cli_build_engine_missing_template_file` | Medium | Template error handling |
| 45 | CLI | `test_cli.py` | `test_cli_build_engine_invalid_template_file` | Medium | Template validation |
| 46 | CLI | `test_cli.py` | `test_cli_main_writes_report_file` | Low | Output handling |
| 47 | CLI | `test_cli.py` | `test_cli_main_prints_to_console` | Low | Output handling |
| 48 | CLI | `test_cli.py` | `test_cli_narrative_requires_model` | Medium | CLI validation |
| 49 | CLI | `test_cli.py` | `test_cli_narrative_missing_file` | Medium | File handling |
| 50 | CLI | `test_cli.py` | `test_cli_narrative_integration` | Low | Integration |
| **NARRATIVE PARSER** |
| 51 | Narrative | `test_narrative.py` | `test_parser_builds_profile_from_json_payload` | Medium | ✅ EXISTS - Core functionality |
| 52 | Narrative | `test_narrative.py` | `test_parser_generates_slug_when_missing` | Medium | ✅ EXISTS - Slug generation |
| 53 | Narrative | `test_narrative.py` | `test_parser_extracts_json_from_wrapped_response` | Medium | ✅ EXISTS - JSON extraction |
| 54 | Narrative | `test_narrative.py` | `test_parser_extract_json_malformed_json` | **High** | JSON extraction fragility |
| 55 | Narrative | `test_narrative.py` | `test_parser_extract_json_no_json_found` | **High** | JSON extraction error handling |
| 56 | Narrative | `test_narrative.py` | `test_parser_extract_json_nested_structures` | Medium | JSON extraction edge cases |
| 57 | Narrative | `test_narrative.py` | `test_parser_slugify_special_characters` | Low | Slug generation edge cases |
| 58 | Narrative | `test_narrative.py` | `test_parser_slugify_empty_name` | **High** | Slug generation edge cases |
| 59 | Narrative | `test_narrative.py` | `test_parser_default_name_fallback` | Medium | Default handling |
| 60 | Narrative | `test_narrative.py` | `test_parser_openai_model_missing_package` | Medium | Dependency handling |
| 61 | Narrative | `test_narrative.py` | `test_parser_openai_model_api_error` | Low | External API errors |
| 62 | Narrative | `test_narrative.py` | `test_prompt_builder_includes_guidance` | Low | ✅ EXISTS - Prompt validation |
| **ANALYSIS ENGINE** |
| 63 | Analysis | `test_analysis.py` | `test_engine_generates_opportunities` | Medium | ✅ EXISTS - Core functionality |
| 64 | Analysis | `test_analysis.py` | `test_high_priority_opportunities_present` | Medium | ✅ EXISTS - Priority logic |
| 65 | Analysis | `test_analysis.py` | `test_engine_find_complementary_pairs_empty` | Low | Edge cases |
| 66 | Analysis | `test_analysis.py` | `test_engine_find_complementary_pairs_single_company` | Low | Edge cases |
| 67 | Analysis | `test_analysis.py` | `test_engine_build_opportunities_no_matches` | Low | Edge cases |
| 68 | Analysis | `test_analysis.py` | `test_engine_register_companies_duplicate_slugs` | **High** | Duplicate handling |
| 69 | Analysis | `test_analysis.py` | `test_engine_profile_missing_company` | **High** | Missing company handling |
| 70 | Analysis | `test_analysis.py` | `test_engine_term_indexing` | Low | Internal state |
| 71 | Analysis | `test_analysis.py` | `test_engine_triad_generation_requires_two_pairs` | Medium | Triad logic |
| 72 | Analysis | `test_analysis.py` | `test_engine_priority_scoring` | Low | Priority logic |
| 73 | Analysis | `test_analysis.py` | `test_engine_expected_outcomes_generation` | Low | Outcome logic |
| 74 | Analysis | `test_analysis.py` | `test_engine_large_dataset_performance` | Low | Performance |
| **TEMPLATE LIBRARY** |
| 75 | Templates | `test_templates.py` | `test_template_library_load_from_file` | Medium | File loading |
| 76 | Templates | `test_templates.py` | `test_template_library_load_from_dict` | Medium | Dict loading |
| 77 | Templates | `test_templates.py` | `test_template_library_template_missing_raises` | **High** | Missing template handling |
| 78 | Templates | `test_templates.py` | `test_template_library_tier_missing_raises` | **High** | Missing tier handling |
| 79 | Templates | `test_templates.py` | `test_template_library_auto_complete_profile` | Medium | Template application |
| 80 | Templates | `test_templates.py` | `test_template_library_group_companies` | Medium | Tiering logic |
| 81 | Templates | `test_templates.py` | `test_template_library_group_companies_no_matches` | Low | Edge cases |
| 82 | Templates | `test_templates.py` | `test_tiering_rule_applies_to_company` | Medium | Rule matching |
| 83 | Templates | `test_templates.py` | `test_tiering_rule_case_insensitive` | Low | Rule matching edge cases |

---

## Summary by Priority

- **High Priority: 25 tests** - Critical bugs, crashes, data loss
- **Medium Priority: 33 tests** - Core functionality, user workflows
- **Low Priority: 25 tests** - Edge cases, robustness, performance

**Total: 83 test cases**

---

## Implementation Checklist

### Phase 1: High Priority (25 tests)
- [ ] Models: Tests 1-2, 5-6, 8
- [x] Graph/Storage: Tests 15-16, 19-20 ✅ IMPLEMENTED
- [x] API: Tests 28-31 ✅ IMPLEMENTED
- [ ] CLI: Tests 40-42
- [ ] Narrative: Tests 54-55, 58
- [ ] Analysis: Tests 68-69
- [ ] Templates: Tests 77-78

### Phase 2: Medium Priority (33 tests)
- [ ] Models: Tests 3-4, 7
- [ ] Graph/Storage: Tests 13-14, 17-18, 21, 24
- [ ] API: Tests 26-27, 32-34
- [ ] CLI: Tests 39, 43-45, 48-49
- [ ] Narrative: Tests 51-53, 56, 59-60
- [ ] Analysis: Tests 63-64, 71
- [ ] Templates: Tests 75-76, 79-80, 82

### Phase 3: Low Priority (25 tests)
- [ ] Models: Tests 9-12
- [ ] Graph/Storage: Tests 22-23, 25
- [ ] API: Tests 35-38
- [ ] CLI: Tests 46-47, 50
- [ ] Narrative: Tests 57, 61-62
- [ ] Analysis: Tests 65-67, 70, 72-74
- [ ] Templates: Tests 81, 83

---

## Notes

- ✅ = Test already exists (may need extension)
- **High** = Prevents crashes/data loss
- **Medium** = Core functionality
- **Low** = Edge cases/robustness

