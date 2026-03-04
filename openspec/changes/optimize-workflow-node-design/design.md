# Design: Workflow Node Architecture Refactor

## Context
Current nodes are monolithic Vue components. This design will break them into a composable set of sub-components and specialized hooks.

## Goals
- **Separation of Concerns**: Logic in Hooks, Presentation in Atomic Components.
- **Visual Excellence**: Implement modern UI patterns (Glassmorphism, Dynamic Shadows).
- **Scalability**: Support multiple node types (Tool, Filter, Visualization) using the same core primitives.

## Decisions
1. **Atoms / Components**:
   - `NodeContainer`: Handles absolute positioning, z-index, and selection-border.
   - `NodeHeader`: Styled area for title, icon, and status indicators.
   - `NodeBody`: Content area with Flex/Grid layout support.
   - `NodeHandle`: The actual connection points, styled with magnification effects.
2. **Logic Hooks**:
   - `useNodeInteraction`: Manages `isHovered`, `isSelected`, `isDragging`.
   - `useNodeState`: Syncs node data with the global Pinia store.
3. **Styling Strategy**:
   - Use CSS variables for themes (Light/Dark).
   - Tailwind for utility-based layout, but Scoped CSS for complex visuals like glows.

## Risks / Trade-offs
- **Refactoring Effort**: Existing nodes need to be ported.
- **Performance**: Many small components might impact initial render if not optimized (use `v-memo` or functional components where possible).

<success_criteria>
- `WorkflowNode.vue` length reduced by 50%.
- New nodes (e.g., `ToolNode`) can be built in < 50 lines of code.
- Zero regression in dragging/selection functionality.
</success_criteria>

<unlocks>
Completing this artifact enables: tasks
</unlocks>
