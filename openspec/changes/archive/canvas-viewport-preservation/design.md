## Context

**Current State:**
The `VueFlowCanvas.vue` component uses `useVueFlow()` composable's `fitView()` function in two watchers (lines 242-252):
- Watch on `nodes.value.length` - triggers `fitView()` when nodes are added
- Watch on `edges.value.length` - triggers `fitView()` when edges are added

These watchers were likely intended to ensure newly added content is visible, but they have the unintended side effect of resetting the user's viewport (zoom and pan position) on every node/edge addition.

**Constraints:**
- Must use Vue Flow's existing API and state management
- Must not break existing Vue Flow controls (the controls component already has a "fit view" button)
- The `fit-view-on-init` prop is already set to `true` for initial load

**Technical Stack:**
- Vue 3 Composition API
- @vue-flow/core for canvas functionality
- Pinia store for workflow state

## Goals / Non-Goals

**Goals:**
- Preserve canvas viewport (zoom level and pan position) when nodes are added
- Preserve canvas viewport when connections (edges) are created
- Maintain the initial `fitView()` behavior on first workflow load (via `fit-view-on-init` prop)
- Keep the existing controls button for manual "fit to view" functionality

**Non-Goals:**
- Adding new UI controls for viewport management (already exists in VueFlow Controls)
- Implementing custom viewport persistence to localStorage
- Changing the behavior of the controls component's fit view button
- Modifying how nodes are positioned when dropped (drag-and-drop behavior)

## Decisions

### Decision 1: Remove automatic `fitView()` watchers entirely

**Rationale:**
- The simplest fix with the least risk
- The `fit-view-on-init` prop already handles the initial fit behavior when a workflow loads
- Users can still trigger fit view manually via the existing controls button
- The watchers provide no value beyond the initial load - in fact, they actively harm UX

**Alternatives Considered:**
1. **Make watchers conditional** (e.g., only fit on first node): Would add complexity without clear benefit
2. **Add a user preference toggle**: Over-engineering for a simple UX issue
3. **Debounce the fitView calls**: Would still cause unwanted viewport resets, just delayed

### Decision 2: Use Vue Flow's built-in viewport state management

**Rationale:**
- Vue Flow already manages viewport state internally (zoom, position)
- The library is designed to preserve viewport state unless explicitly changed
- No need to add custom state management for viewport

**Implementation:**
Simply remove the two `watch()` calls that trigger `fitView()` on node/edge length changes.

### Decision 3: Keep `fit-view-on-init` prop

**Rationale:**
- Provides good UX for initial workflow load - fits content to view
- Only runs once on mount, not on subsequent changes
- Aligns with typical canvas application behavior

## Risks / Trade-offs

**Risk:** New nodes added outside the current viewport may not be visible
**Mitigation:** This is expected behavior - users can pan to find new nodes or use the controls button to fit view. The alternative (resetting viewport) is worse UX.

**Risk:** Users who relied on auto-fit for workflow discovery may be confused
**Mitigation:** The controls button is prominent and discoverable. Consider adding a tooltip or hint if needed in a future update.

**Trade-off:** Simplicity vs. automatic visibility
**Analysis:** We're choosing manual control over automatic behavior. This aligns with professional tools (Figma, Miro, etc.) where users control their viewport.

## Migration Plan

**Steps:**
1. Remove the two `watch()` blocks from `VueFlowCanvas.vue` (lines 242-252)
2. Test by adding nodes to a workflow - verify viewport doesn't reset
3. Test by creating connections - verify viewport doesn't reset
4. Test initial workflow load - verify `fit-view-on-init` still works
5. Test manual "fit view" button in controls - verify it works

**Rollback Strategy:**
Simply revert the file change if issues arise. The change is isolated to a single file with minimal code removal.

## Open Questions

None - the change is straightforward and well-scoped.
