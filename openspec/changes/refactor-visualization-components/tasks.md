# Implementation Tasks: Refactor Visualization Components

## 1. Foundation and Testing Setup

- [ ] 1.1 Add feature flag `VITE_USE_NEW_VIEWERS` to environment configuration
- [ ] 1.2 Update `.env.development` and `.env.production` with feature flag defaults
- [ ] 1.3 Install testing dependencies for composables (Vitest, @vue/test-utils if not present)
- [ ] 1.4 Create `tests/unit/composables/` directory structure
- [ ] 1.5 Run baseline E2E tests to ensure all current tests pass before changes
- [ ] 1.6 Take screenshots of all viewer types for visual regression baseline

## 2. Phase 1: Composables Layer

### 2.1 useECharts Composable

- [ ] 2.1.1 Create `src/composables/useECharts.ts` file
- [ ] 2.1.2 Implement ECharts initialization logic with container ref
- [ ] 2.1.3 Implement automatic disposal on component unmount
- [ ] 2.1.4 Implement setOption method for updating chart
- [ ] 2.1.5 Implement resize handler with automatic window resize listener
- [ ] 2.1.6 Add event handler attachment/detachment methods
- [ ] 2.1.7 Add theme support for initialization
- [ ] 2.1.8 Add TypeScript types for all methods and return values
- [ ] 2.1.9 Write unit tests for useECharts (mount, dispose, setOption, resize)
- [ ] 2.1.10 Run unit tests and ensure 100% coverage for useECharts

### 2.2 useChartSelection Composable

- [ ] 2.2.1 Create `src/composables/useChartSelection.ts` file
- [ ] 2.2.2 Implement selection state using reactive Set or ref
- [ ] 2.2.3 Implement selectedCount computed property
- [ ] 2.2.4 Implement hasSelection computed property
- [ ] 2.2.5 Implement addSelection method
- [ ] 2.2.6 Implement removeSelection method
- [ ] 2.2.7 Implement clearSelection method
- [ ] 2.2.8 Implement isItemSelected method for checking specific items
- [ ] 2.2.9 Add selection change event emission
- [ ] 2.2.10 Add TypeScript types for selection state and methods
- [ ] 2.2.11 Write unit tests for all selection operations
- [ ] 2.2.12 Run unit tests and ensure 100% coverage

### 2.3 useFullscreen Composable

- [ ] 2.3.1 Create `src/composables/useFullscreen.ts` file
- [ ] 2.3.2 Implement fullscreen state ref
- [ ] 2.3.3 Implement toggleFullscreen method
- [ ] 2.3.4 Implement enterFullscreen method
- [ ] 2.3.5 Implement exitFullscreen method
- [ ] 2.3.6 Add event listeners for fullscreen change (ESC key support)
- [ ] 2.3.7 Add TypeScript types
- [ ] 2.3.8 Write unit tests for fullscreen operations
- [ ] 2.3.9 Run unit tests and ensure 100% coverage

### 2.4 useChartConfig Composable

- [ ] 2.4.1 Create `src/composables/useChartConfig.ts` file
- [ ] 2.4.2 Implement generic config state management
- [ ] 2.4.3 Implement mergeConfig method for merging user config with defaults
- [ ] 2.4.4 Implement updateConfig method
- [ ] 2.4.5 Implement resetConfig method
- [ ] 2.4.6 Implement validateConfig method
- [ ] 2.4.7 Add config change event emission
- [ ] 2.4.8 Add TypeScript types with generic parameter
- [ ] 2.4.9 Write unit tests for config operations
- [ ] 2.4.10 Run unit tests and ensure 100% coverage

### 2.5 useChartExport Composable

- [ ] 2.5.1 Create `src/composables/useChartExport.ts` file
- [ ] 2.5.2 Implement exportToPNG method
- [ ] 2.5.3 Implement exportToSVG method
- [ ] 2.5.4 Implement exportData method for CSV/JSON export
- [ ] 2.5.5 Add filename generation logic
- [ ] 2.5.6 Add TypeScript types for export methods
- [ ] 2.5.7 Write unit tests for export operations
- [ ] 2.5.8 Run unit tests and ensure 100% coverage

## 3. Phase 2: Base Component

### 3.1 BaseEChartsViewer Component

- [ ] 3.1.1 Create `src/components/visualization/BaseEChartsViewer.vue` file
- [ ] 3.1.2 Implement template with toolbar, config, chart, and selection slots
- [ ] 3.1.3 Integrate useECharts composable
- [ ] 3.1.4 Integrate useFullscreen composable
- [ ] 3.1.5 Integrate useChartSelection composable
- [ ] 3.1.6 Add chartContainer ref
- [ ] 3.1.7 Add edit mode prop and conditional rendering of config slot
- [ ] 3.1.8 Add data prop (TableData | null)
- [ ] 3.1.9 Add config prop with generic type
- [ ] 3.1.10 Define emits for selectionChange, configChange, export
- [ ] 3.1.11 Expose chart instance and state via defineExpose
- [ ] 3.1.12 Add responsive styles
- [ ] 3.1.13 Write integration tests for BaseEChartsViewer
- [ ] 3.1.14 Run tests and ensure they pass

## 4. Phase 3: Viewer Migration

### 4.1 ScatterPlotViewer Migration

- [ ] 4.1.1 Read current `ScatterPlotViewer.vue` implementation
- [ ] 4.1.2 Create backup of original file
- [ ] 4.1.3 Refactor ScatterPlotViewer to use BaseEChartsViewer
- [ ] 4.1.4 Move chart rendering logic to useECharts
- [ ] 4.1.5 Move selection logic to useChartSelection
- [ ] 4.1.6 Move fullscreen logic to useFullscreen
- [ ] 4.1.7 Extract toolbar content to toolbar slot
- [ ] 4.1.8 Extract config panel to config slot
- [ ] 4.1.9 Extract selection info to selection slot
- [ ] 4.1.10 Test refactored ScatterPlotViewer in isolation
- [ ] 4.1.11 Run E2E tests with feature flag enabled for ScatterPlotViewer
- [ ] 4.1.12 Perform visual regression comparison
- [ ] 4.1.13 Fix any issues found during testing
- [ ] 4.1.14 Enable feature flag for ScatterPlotViewer in production config

### 4.2 HeatmapViewer Migration

- [ ] 4.2.1 Read current `HeatmapViewer.vue` implementation
- [ ] 4.2.2 Create backup of original file
- [ ] 4.2.3 Refactor HeatmapViewer to use BaseEChartsViewer
- [ ] 4.2.4 Move chart rendering logic to useECharts
- [ ] 4.2.5 Move selection logic to useChartSelection
- [ ] 4.2.6 Move fullscreen logic to useFullscreen
- [ ] 4.2.7 Extract toolbar, config, and selection to slots
- [ ] 4.2.8 Test refactored HeatmapViewer in isolation
- [ ] 4.2.9 Run E2E tests with feature flag enabled for HeatmapViewer
- [ ] 4.2.10 Perform visual regression comparison
- [ ] 4.2.11 Fix any issues found during testing
- [ ] 4.2.12 Enable feature flag for HeatmapViewer in production config

### 4.3 VolcanoPlotViewer Migration

- [ ] 4.3.1 Read current `VolcanoPlotViewer.vue` implementation
- [ ] 4.3.2 Create backup of original file
- [ ] 4.3.3 Refactor VolcanoPlotViewer to use BaseEChartsViewer
- [ ] 4.3.4 Move chart rendering logic to useECharts
- [ ] 4.3.5 Move selection logic to useChartSelection
- [ ] 4.3.6 Move fullscreen logic to useFullscreen
- [ ] 4.3.7 Extract toolbar, config, and selection to slots
- [ ] 4.3.8 Test refactored VolcanoPlotViewer in isolation
- [ ] 4.3.9 Run E2E tests with feature flag enabled for VolcanoPlotViewer
- [ ] 4.3.10 Perform visual regression comparison
- [ ] 4.3.11 Fix any issues found during testing
- [ ] 4.3.12 Enable feature flag for VolcanoPlotViewer in production config

### 4.4 SpectrumViewer Migration

- [ ] 4.4.1 Read current `SpectrumViewer.vue` implementation
- [ ] 4.4.2 Create backup of original file
- [ ] 4.4.3 Refactor SpectrumViewer to use BaseEChartsViewer
- [ ] 4.4.4 Move chart rendering logic to useECharts
- [ ] 4.4.5 Move selection logic to useChartSelection
- [ ] 4.4.6 Move fullscreen logic to useFullscreen
- [ ] 4.4.7 Extract toolbar, config, and selection to slots
- [ ] 4.4.8 Test refactored SpectrumViewer in isolation
- [ ] 4.4.9 Run E2E tests with feature flag enabled for SpectrumViewer
- [ ] 4.4.10 Perform visual regression comparison
- [ ] 4.4.11 Fix any issues found during testing
- [ ] 4.4.12 Enable feature flag for SpectrumViewer in production config

### 4.5 FeatureMapViewer Migration

- [ ] 4.5.1 Read current `FeatureMapViewer.vue` implementation
- [ ] 4.5.2 Create backup of original file
- [ ] 4.5.3 Refactor FeatureMapViewer to use BaseEChartsViewer
- [ ] 4.5.4 Move chart rendering logic to useECharts
- [ ] 4.5.5 Move selection logic to useChartSelection
- [ ] 4.5.6 Move fullscreen logic to useFullscreen
- [ ] 4.5.7 Extract toolbar, config, and selection to slots
- [ ] 4.5.8 Test refactored FeatureMapViewer in isolation
- [ ] 4.5.9 Run E2E tests with feature flag enabled for FeatureMapViewer
- [ ] 4.5.10 Perform visual regression comparison
- [ ] 4.5.11 Fix any issues found during testing
- [ ] 4.5.12 Enable feature flag for FeatureMapViewer in production config

## 5. Phase 4: InteractiveNode Refactoring

### 5.1 Extract NodeHeader Component

- [ ] 5.1.1 Create `src/components/visualization/NodeHeader.vue` file
- [ ] 5.1.2 Extract header template from InteractiveNode.vue
- [ ] 5.1.3 Extract header styles from InteractiveNode.vue
- [ ] 5.1.4 Define props interface (label, visualizationType, nodeState, loading, error)
- [ ] 5.1.5 Define emits interface (editToggle, retry, fullscreen)
- [ ] 5.1.6 Implement icon selection logic based on nodeState
- [ ] 5.1.7 Add TypeScript types for props and emits
- [ ] 5.1.8 Write unit tests for NodeHeader
- [ ] 5.1.9 Run tests and ensure they pass

### 5.2 Extract NodeConfigPanel Component

- [ ] 5.2.1 Create `src/components/visualization/NodeConfigPanel.vue` file
- [ ] 5.2.2 Extract config panel template from InteractiveNode.vue
- [ ] 5.2.3 Extract config panel styles from InteractiveNode.vue
- [ ] 5.2.4 Define props interface (visualizationType, columns, axisMapping, config)
- [ ] 5.2.5 Define emits interface (configChange)
- [ ] 5.2.6 Implement tab rendering logic
- [ ] 5.2.7 Implement data mapping config rendering
- [ ] 5.2.8 Implement appearance config rendering
- [ ] 5.2.9 Implement export config rendering
- [ ] 5.2.10 Add TypeScript types
- [ ] 5.2.11 Write unit tests for NodeConfigPanel
- [ ] 5.2.12 Run tests and ensure they pass

### 5.3 Extract useNodeStateManager Composable

- [ ] 5.3.1 Create `src/composables/useNodeStateManager.ts` file
- [ ] 5.3.2 Extract state management logic from InteractiveNode.vue
- [ ] 5.3.3 Implement nodeState computed property (idle, loading, error, ready)
- [ ] 5.3.4 Implement errorMessage computed property
- [ ] 5.3.5 Implement editMode state and toggle method
- [ ] 5.3.6 Implement hasData computed property
- [ ] 5.3.7 Implement hasUpstreamConnection computed property
- [ ] 5.3.8 Implement retry method
- [ ] 5.3.9 Add TypeScript types
- [ ] 5.3.10 Write unit tests for useNodeStateManager
- [ ] 5.3.11 Run tests and ensure they pass

### 5.4 Refactor InteractiveNode

- [ ] 5.4.1 Create backup of original `InteractiveNode.vue`
- [ ] 5.4.2 Remove extracted header code and use NodeHeader component
- [ ] 5.4.3 Remove extracted config panel code and use NodeConfigPanel component
- [ ] 5.4.4 Remove extracted state logic and use useNodeStateManager
- [ ] 5.4.5 Simplify template to use new components
- [ ] 5.4.6 Keep orchestration logic (data flow, viewer loading, event handling)
- [ ] 5.4.7 Ensure props interface remains unchanged
- [ ] 5.4.8 Ensure emits interface remains unchanged
- [ ] 5.4.9 Verify file size is reduced to ~300 lines
- [ ] 5.4.10 Run E2E tests for InteractiveNode
- [ ] 5.4.11 Perform visual regression testing
- [ ] 5.4.12 Fix any issues found during testing
- [ ] 5.4.13 Verify backward compatibility with existing workflows

## 6. Phase 5: Configuration and Utilities

### 6.1 Type Definitions

- [ ] 6.1.1 Review current `types/visualization.ts`
- [ ] 6.1.2 Add ScatterConfig interface
- [ ] 6.1.3 Add HeatmapConfig interface
- [ ] 6.1.4 Add VolcanoConfig interface
- [ ] 6.1.5 Add SpectrumConfig interface
- [ ] 6.1.6 Add FeatureMapConfig interface
- [ ] 6.1.7 Add base ChartConfig interface
- [ ] 6.1.8 Ensure all configs extend ChartConfig appropriately
- [ ] 6.1.9 Run TypeScript type checking (`tsc --noEmit`)
- [ ] 6.1.10 Fix any type errors

### 6.2 Configuration Utilities

- [ ] 6.2.1 Create `src/utils/chart-configs.ts` file
- [ ] 6.2.2 Implement default configuration objects for each chart type
- [ ] 6.2.3 Implement config validation functions
- [ ] 6.2.4 Implement config merging utilities
- [ ] 6.2.5 Add column reference validation logic
- [ ] 6.2.6 Add numeric range validation logic
- [ ] 6.2.7 Add TypeScript types for utility functions
- [ ] 6.2.8 Write unit tests for config utilities
- [ ] 6.2.9 Run tests and ensure they pass

## 7. Phase 6: Cleanup and Documentation

### 7.1 Remove Feature Flags

- [ ] 7.1.1 Verify all viewers are using new implementation
- [ ] 7.1.2 Remove feature flag checks from all viewer components
- [ ] 7.1.3 Remove VITE_USE_NEW_VIEWERS from environment files
- [ ] 7.1.4 Remove feature flag imports and usage
- [ ] 7.1.5 Run full test suite to ensure nothing breaks
- [ ] 7.1.6 Commit cleanup changes

### 7.2 Remove Dead Code

- [ ] 7.2.1 Identify all backup files created during migration
- [ ] 7.2.2 Delete backup files
- [ ] 7.2.3 Search for any remaining old implementation code
- [ ] 7.2.4 Remove unused imports across all files
- [ ] 7.2.5 Run ESLint to find and fix issues
- [ ] 7.2.6 Run Prettier to format all files
- [ ] 7.2.7 Run TypeScript type checking
- [ ] 7.2.8 Run full test suite

### 7.3 Update Documentation

- [ ] 7.3.1 Update `ARCHITECTURE.md` with new component structure
- [ ] 7.3.2 Document composable APIs in code comments
- [ ] 7.3.3 Create README for composables directory
- [ ] 7.3.4 Add JSDoc comments to all composable functions
- [ ] 7.3.5 Document BaseEChartsViewer usage
- [ ] 7.3.6 Update component documentation
- [ ] 7.3.7 Add examples for creating new viewers

### 7.4 Final Testing

- [ ] 7.4.1 Run full E2E test suite
- [ ] 7.4.2 Run all unit tests
- [ ] 7.4.3 Perform final visual regression check
- [ ] 7.4.4 Test all viewer types manually
- [ ] 7.4.5 Test InteractiveNode functionality
- [ ] 7.4.6 Test node-to-node data flow
- [ ] 7.4.7 Test configuration changes
- [ ] 7.4.8 Test export functionality
- [ ] 7.4.9 Test fullscreen functionality
- [ ] 7.4.10 Test selection functionality
- [ ] 7.4.11 Verify no performance degradation
- [ ] 7.4.12 Check console for errors or warnings
- [ ] 7.4.13 Verify accessibility (keyboard navigation, screen readers)

## 8. Verification and Deployment

- [ ] 8.1 Verify all E2E tests pass
- [ ] 8.2 Verify code coverage is maintained or improved
- [ ] 8.3 Verify TypeScript compilation succeeds
- [ ] 8.4 Verify build succeeds without errors
- [ ] 8.5 Verify bundle size has not significantly increased
- [ ] 8.6 Create pull request with all changes
- [ ] 8.7 Get code review approval
- [ ] 8.8 Merge to main branch
- [ ] 8.9 Deploy to staging environment
- [ ] 8.10 Perform smoke testing on staging
- [ ] 8.11 Deploy to production
- [ ] 8.12 Monitor production for issues
- [ ] 8.13 Create completion report with metrics

## Summary Metrics (to be completed after implementation)

- [ ] Total lines of code reduced: ____
- [ ] Code duplication reduced from 60% to: ____%
- [ ] Number of composables created: 6
- [ ] Number of components refactored: 7
- [ ] Test coverage maintained at: ____%
- [ ] E2E tests passing: ____ / ____
- [ ] Performance impact: ____%
