# Tasks: Workflow Node Design Optimization

## 1. UI Infrastructure (Atoms)
- [x] 1.1 Create `components/workflow/node/NodeContainer.vue` (Handles layout/selection)
- [x] 1.2 Create `components/workflow/node/NodeHeader.vue` (Handles title/pulse-status)
- [x] 1.3 Create `components/workflow/node/NodeBody.vue` (Flex/Grid wrapper)
- [x] 1.4 Create `components/workflow/node/NodePort.vue` (Handles magnetic hover/glow)

## 2. Logic & State (Composables)
- [x] 2.1 Create `composables/useNodeInteraction.ts` (Selection/Hover/Drag state)
- [x] 2.2 Create `composables/useNodeThemes.ts` (Light/Dark/Glassmorphism logic)

## 3. Component Refactoring (Integration)
- [x] 3.1 Refactor `WorkflowNode.vue` to use new primitives and hooks.
- [x] 3.2 Update `ToolNode.vue` to use the new architecture.

## 4. Visual Polish & Verification
- [x] 4.1 Implement Scoped CSS for Backdrop-Blur and Pulsing Animations.
- [x] 4.2 Verify dragging and connection snapping in the browser.

<success_criteria>
- All 4 atom components created and functional.
- `WorkflowNode.vue` logic moved to composables.
- Visuals match the "Aesthetics Spec" (Glassmorphism, Port Magnification).
</success_criteria>