# Design: Refactor Visualization Components

## Context

### Current State
The visualization system consists of 12 Vue components totaling 4,739 lines with significant code duplication:

**Code Duplication Analysis:**
- **ECharts Initialization**: Repeated 6 times across ScatterPlotViewer, HeatmapViewer, VolcanoPlotViewer, SpectrumViewer, FeatureMapViewer
- **Selection Management**: Each component implements its own selection state, handlers, and clearing logic
- **Event Handling**: Brush/click events duplicated with minor variations
- **Configuration Panels**: Each viewer has inline config forms with repeated select/dropdown patterns
- **Export Logic**: Export handling scattered across components
- **Fullscreen Toggle**: Same implementation in every viewer

**Largest Component:**
- `InteractiveNode.vue`: 874 lines - handles node state, config panels, data mapping, viewer coordination, and export

### Existing Patterns
The project already uses Vue 3 Composition API with some composables in `src/composables/`:
- `useCanvasControls.ts`
- `useContextMenu.ts`
- `useHistoryManager.ts`
- `useKeyboardShortcuts.ts`
- `useNodeInteraction.ts`
- `useNodeThemes.ts`

However, **no visualization-specific composables exist**.

### Constraints
- **No Breaking Changes**: External APIs must remain unchanged
- **Test Coverage**: Must maintain existing E2E test coverage
- **Performance**: No performance regression
- **Incremental Deployment**: Must be able to ship incrementally

## Goals / Non-Goals

**Goals:**
1. Reduce code duplication from ~60% to <10%
2. Extract reusable visualization composables following Vue 3 best practices
3. Create base viewer component to eliminate repeated structure
4. Split InteractiveNode.vue into focused, single-responsibility components
5. Maintain 100% backward compatibility with existing functionality
6. Improve maintainability and reduce onboarding time for new developers

**Non-Goals:**
1. Changing user-facing behavior or visual appearance
2. Modifying backend APIs or data structures
3. Adding new visualization types
4. Changing the node-based workflow architecture
5. Performance optimization (beyond avoiding degradation)
6. TypeScript refactoring (types stay as-is unless needed for new code)

## Decisions

### 1. Composable-First Architecture

**Decision:** Extract all shared logic into composables before creating base components.

**Rationale:**
- Vue 3 Composition API is designed for this use case
- Composables are easier to test than components
- Allows gradual migration (one component at a time)
- More flexible than inheritance (can mix and match)
- Aligns with existing project patterns

**Alternatives Considered:**
- **Inheritance**: Rejected - Vue 3 favors composition over inheritance
- **Mixins**: Rejected - Deprecated pattern in Vue 3, unclear data flow
- **Helper Functions**: Rejected - Loses reactivity and lifecycle hooks

### 2. Incremental Migration with Feature Flags

**Decision:** Use a feature flag to switch between old and new implementations during migration.

**Rationale:**
- Allows A/B testing during migration
- Easy rollback if issues arise
- Can ship incrementally without big-bang release
- Reduces risk of breaking production

**Implementation:**
```typescript
const config = useRuntimeConfig()
const useNewViewers = config.public.VITE_USE_NEW_VIEWERS === 'true'
```

### 3. Base Component Using Composition

**Decision:** Create `BaseEChartsViewer.vue` that uses the new composables internally.

**Rationale:**
- Provides common structure (toolbar, chart container, selection info)
- Reduces boilerplate in specific viewers
- Still allows customization via slots and props
- Viewers can opt-in to features they need

**Structure:**
```vue
<BaseEChartsViewer>
  <template #toolbar>Custom toolbar controls</template>
  <template #config>Custom config panel</template>
  <template #chart>Chart handled by base</template>
  <template #selection-info>Custom selection display</template>
</BaseEChartsViewer>
```

### 4. Type-Safe Configuration System

**Decision:** Centralize configuration types and validation using TypeScript.

**Rationale:**
- Catches configuration errors at compile time
- Provides better IDE autocomplete
- Documents expected configuration structure
- Enables future config migration tools

**Implementation:**
```typescript
// types/visualization.ts
export interface ChartConfig {
  type: ChartType
  title?: string
  colorScheme?: string
  axisMapping?: AxisMapping
  // ... common config fields
}

export interface ScatterConfig extends ChartConfig {
  type: 'scatter'
  xColumn: string
  yColumn: string
  // ... scatter-specific config
}
```

### 5. Testing Strategy

**Decision:** Use a testing pyramid with E2E tests as the safety net.

**Levels:**
1. **Unit Tests**: Test composables in isolation (fast, focused)
2. **Integration Tests**: Test component + composable interaction
3. **E2E Tests**: Verify complete user workflows (slow, comprehensive)

**Rationale:**
- Composables are pure functions - easy to unit test
- E2E tests already exist and provide regression safety
- Integration tests catch component-level issues
- Visual regression tests ensure no UI changes

### 6. InteractiveNode Split Strategy

**Decision:** Split InteractiveNode into 4 focused pieces using extract method refactoring.

**Pieces:**
1. `InteractiveNode.vue` (~300 lines) - Orchestration and state
2. `NodeHeader.vue` (~100 lines) - Header with title and actions
3. `NodeConfigPanel.vue` (~200 lines) - Configuration tabs and forms
4. `useNodeStateManager.ts` (~150 lines) - Node state management logic

**Rationale:**
- Each piece has single responsibility
- Can be tested independently
- Easier to understand and modify
- Reduces cognitive load

## Architecture

### Phase 1: Composable Layer

```
src/composables/
├── useECharts.ts              # ECharts lifecycle (init, resize, dispose)
├── useChartSelection.ts       # Selection state management
├── useChartExport.ts          # Export functionality
├── useChartConfig.ts          # Configuration management
├── useFullscreen.ts           # Fullscreen toggle
└── useChartTools.ts           # Zoom, pan, reset (utility)
```

**API Design:**
```typescript
// useECharts.ts
export function useECharts(container: Ref<HTMLElement | undefined>) {
  const chart = shallowRef<echarts.ECharts | null>(null)
  const isReady = computed(() => chart.value !== null)

  const init = () => {
    if (!container.value) return
    chart.value = echarts.init(container.value, theme)
  }

  const dispose = () => {
    chart.value?.dispose()
    chart.value = null
  }

  const setOption = (option: EChartsOption) => {
    chart.value?.setOption(option, notMerge)
  }

  onMounted(init)
  onUnmounted(dispose)

  return { chart, isReady, init, dispose, setOption }
}
```

### Phase 2: Component Layer

```
src/components/visualization/
├── BaseEChartsViewer.vue     # Base component (new)
├── viewers/
│   ├── ScatterPlotViewer.vue    # Refactored
│   ├── HeatmapViewer.vue        # Refactored
│   ├── VolcanoPlotViewer.vue    # Refactored
│   ├── SpectrumViewer.vue       # Refactored
│   └── FeatureMapViewer.vue     # Refactored
└── node/
    ├── InteractiveNode.vue      # Refactored
    ├── NodeHeader.vue           # New
    ├── NodeConfigPanel.vue      # New
    └── useNodeStateManager.ts   # New
```

**BaseEChartsViewer Structure:**
```vue
<template>
  <div class="base-viewer" :class="{ fullscreen: isFullscreen }">
    <div v-if="$slots.toolbar" class="viewer-toolbar">
      <slot name="toolbar" :fullscreen="isFullscreen" :toggle-fullscreen="toggleFullscreen" />
    </div>

    <div v-if="editMode && $slots.config" class="config-panel">
      <slot name="config" />
    </div>

    <div ref="chartContainer" class="chart-container" />

    <div v-if="hasSelection && $slots.selection" class="selection-info">
      <slot name="selection" :selected-count="selectedCount" :clear-selection="clearSelection" />
    </div>
  </div>
</template>

<script setup lang="ts">
const { chart, isReady } = useECharts(chartContainer)
const { isFullscreen, toggleFullscreen } = useFullscreen()
const { selectedCount, clearSelection } = useChartSelection()

defineExpose({ chart, isReady })
</script>
```

### Phase 3: Configuration Layer

```
src/utils/
└── chart-configs.ts           # Config validators and defaults

src/types/
└── visualization.ts           # Extended with new types
```

## Migration Plan

### Phase 1: Foundation (Week 1)
1. Create `useECharts` composable with tests
2. Create `useChartSelection` composable with tests
3. Create `useFullscreen` composable with tests
4. Add feature flag: `VITE_USE_NEW_VIEWERS`

**Success Criteria:**
- All composables have unit tests with 100% coverage
- E2E tests still pass with feature flag off

### Phase 2: Base Component (Week 2)
1. Create `BaseEChartsViewer.vue`
2. Write integration tests for base component
3. Update one simple viewer (e.g., ScatterPlotViewer)
4. Run E2E tests with feature flag on for that viewer

**Success Criteria:**
- ScatterPlotViewer works identically with old and new implementation
- No visual regression
- All tests pass

### Phase 3: Migrate Viewers (Week 3-4)
Migrate remaining viewers one at a time:
1. HeatmapViewer
2. VolcanoPlotViewer
3. SpectrumViewer
4. FeatureMapViewer

For each viewer:
1. Refactor to use BaseEChartsViewer
2. Run unit tests
3. Run integration tests
4. Run E2E tests
5. Visual regression check
6. Enable feature flag for that viewer

**Rollback Strategy:**
- If any viewer fails tests, revert that specific viewer
- Continue with other viewers
- Feature flag allows per-viewer control

### Phase 4: Split InteractiveNode (Week 5)
1. Extract `NodeHeader.vue`
2. Extract `NodeConfigPanel.vue`
3. Extract `useNodeStateManager.ts`
4. Update InteractiveNode.vue to use new pieces
5. Run all tests

**Success Criteria:**
- InteractiveNode.vue reduced to ~300 lines
- All E2E tests pass
- No functional changes

### Phase 5: Cleanup (Week 6)
1. Remove feature flags (all viewers using new implementation)
2. Remove dead code (old implementations)
3. Update documentation
4. Final E2E test run

## Risks / Trade-offs

### Risk 1: Breaking Existing Functionality
**Impact**: High - Could break production visualizations
**Likelihood**: Medium - Complex refactoring has risks

**Mitigation:**
- Feature flags allow instant rollback
- E2E tests provide regression safety
- Incremental migration limits blast radius
- Visual regression tests catch UI changes

### Risk 2: Performance Regression
**Impact**: Medium - Could slow down rendering
**Likelihood**: Low - Composables are lightweight

**Mitigation:**
- Benchmark performance before and after
- Use `shallowRef` for ECharts instance (no deep reactivity)
- Profile each migrated viewer
- Revert if performance degrades >5%

### Risk 3: Increased Complexity During Migration
**Impact**: Medium - Codebase has both old and new patterns temporarily
**Likelihood**: High - Migration period will have mixed code

**Mitigation:**
- Clear naming: `ScatterPlotViewer.vue` (old) vs `ScatterPlotViewerNew.vue` (new)
- Feature flag keeps old code as default
- Document migration status in code comments
- Complete migration quickly (don't leave it half-done)

### Risk 4: TypeScript Type Errors
**Impact**: Low - Type errors caught at compile time
**Likelihood**: Medium - New types may not match existing patterns

**Mitigation:**
- Use `any` temporarily if needed, fix later
- Incremental type checking (one file at a time)
- Leverage IDE for type checking as you go
- Run `tsc --noEmit` after each change

### Trade-off 1: More Files vs. More Lines
**Choice**: More files with fewer lines each

**Rationale:**
- Smaller files are easier to understand
- Easier to find specific functionality
- Better for code reviews (smaller diffs)
- Aligns with Vue 3 best practices

**Downside:**
- More files to navigate
- Some overhead from imports

### Trade-off 2: Abstraction vs. Simplicity
**Choice**: Introduce abstraction layers (composables, base component)

**Rationale:**
- Reduces duplication long-term
- Easier to add new viewers
- Centralized bug fixes

**Downside:**
- More indirection to understand
- Learning curve for new pattern

## Open Questions

1. **Should we create a `viewers/` subdirectory?**
   - **Current**: All viewers in `visualization/` root
   - **Proposal**: Move to `visualization/viewers/` for better organization
   - **Decision**: Deferred - Can do this as a separate cleanup step

2. **Should we extract configuration to separate JSON files?**
   - **Current**: Config defaults inline in components
   - **Proposal**: Move to `config/chart-defaults.json`
   - **Decision**: No - Keep in TypeScript for type safety

3. **Should we use Pinia for shared state?**
   - **Current**: Local component state with props/emits
   - **Proposal**: Use Pinia for selection state across viewers
   - **Decision**: No - Selection is per-viewer, not global. Keep local.

4. **What ECharts version should we target?**
   - **Current**: Check package.json (need to verify)
   - **Proposal**: Ensure composables work with current version
   - **Decision**: Must verify current version in implementation

5. **Should we create storybook stories for viewers?**
   - **Current**: No visual component documentation
   - **Proposal**: Add Storybook for all viewers
   - **Decision**: Deferred - Good idea but out of scope for this refactor
