# Proposal: Refactor Visualization Components

## Why

The visualization components in `TDEase-FrontEnd/src/components/visualization/` suffer from severe maintainability issues: **~60% code duplication**, lack of abstraction, and high coupling. With 4,739 lines across 12 files and the largest file (InteractiveNode.vue) at 874 lines, the codebase is difficult to maintain, test, and extend. Each viewer component duplicates ECharts initialization, selection management, and configuration logic, making changes error-prone and time-consuming.

## What Changes

### Phase 1: Extract Reusable Composables (Low Risk)
- Create `useECharts` composable for ECharts lifecycle management
- Create `useChartSelection` composable for unified selection state management
- Create `useChartExport` composable for export functionality
- Create `useChartConfig` composable for configuration management
- Create `useFullscreen` composable for fullscreen toggle logic

### Phase 2: Create Base Viewer Component (Medium Risk)
- Create `BaseEChartsViewer.vue` as a foundational component
- Migrate 6 viewer components to extend base component:
  - ScatterPlotViewer.vue
  - HeatmapViewer.vue
  - VolcanoPlotViewer.vue
  - SpectrumViewer.vue
  - FeatureMapViewer.vue
  - Any new chart viewers

### Phase 3: Split InteractiveNode.vue (High Risk)
- Extract `NodeHeader.vue` component
- Extract `NodeConfigPanel.vue` component
- Extract `NodeStateManager.ts` composable
- Reduce InteractiveNode.vue from 874 lines to ~300 lines

### Phase 4: Consolidate Configuration Logic
- Create centralized configuration types in `types/visualization.ts`
- Extract configuration validators to `utils/chart-configs.ts`
- Standardize config propagation patterns

## Capabilities

### New Capabilities

- `echarts-abstraction`: Unified ECharts lifecycle, initialization, event handling, and disposal management through reusable composables
- `chart-selection-system`: Consistent selection state management across all visualization types with unified API
- `chart-config-management`: Centralized configuration handling with type safety and validation
- `modular-viewer-architecture`: Base viewer component that provides common functionality (fullscreen, export, config) to all specific viewers
- `node-component-modularization`: Split monolithic InteractiveNode into focused, single-responsibility components

### Modified Capabilities

None - This is purely an internal refactoring. External APIs and user-facing behavior remain unchanged.

## Impact

### Affected Code
- **Frontend**: `TDEase-FrontEnd/src/components/visualization/` (12 files, ~4,700 lines)
- **Composables**: `TDEase-FrontEnd/src/composables/` (add 5 new files)
- **Types**: `TDEase-FrontEnd/src/types/visualization.ts` (expand)
- **Utils**: `TDEase-FrontEnd/src/utils/` (add chart-configs.ts)

### Dependencies
- No new external dependencies
- Better utilization of existing Vue 3 Composition API
- Improved ECharts integration patterns

### Testing Strategy
- **E2E Tests**: Verify all visualization types render and interact correctly
- **Unit Tests**: Test new composables in isolation
- **Visual Regression**: Ensure no visual changes in existing viewers
- **Integration Tests**: Verify node-to-node data flow remains intact

### Risk Mitigation
- **Incremental Migration**: One component at a time with full test validation
- **Feature Flags**: Optional flag to switch between old and new implementations during migration
- **Backward Compatibility**: Old components remain functional until fully migrated
- **Test Coverage**: Maintain 100% coverage of affected code paths

### Expected Outcomes
- **Code Reduction**: ~2,000 lines eliminated through deduplication
- **Maintainability**: 60% reduction in code duplication
- **Onboarding Time**: 50% faster for new developers
- **Bug Reduction**: Centralized logic = fewer places for bugs to hide
- **Feature Velocity**: New viewers require 50% less code
