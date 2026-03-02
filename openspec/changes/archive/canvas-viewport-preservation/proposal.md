## Why

When users add nodes to the workflow canvas or create connections between nodes, the canvas viewport (zoom level and pan position) is automatically reset to fit all content. This creates a jarring user experience where manual zoom/pan adjustments are lost immediately after any canvas modification, making it difficult to work with large workflows or maintain a focused view while editing.

## What Changes

- **Remove automatic `fitView()` calls on node/edge addition**: The watchers that trigger `fitView()` when nodes or edges are added will be removed or made conditional
- **Add viewport state persistence**: Canvas zoom and pan position will be preserved during node/edge operations
- **Optional: Add manual fit view controls**: Users can explicitly trigger "fit to view" via existing controls button or keyboard shortcut

## Capabilities

### New Capabilities

- `canvas-viewport-preservation`: Ensures canvas zoom level and pan/offset position are preserved during node and edge operations, only resetting when explicitly requested by the user

### Modified Capabilities

None (this is a new capability for the canvas system)

## Impact

- **Affected Components**: `TDEase-FrontEnd/src/components/workflow/VueFlowCanvas.vue`
- **User Experience**: Users will no longer lose their viewport context when adding nodes or connections
- **Backward Compatibility**: Fully backward compatible; only removes unwanted auto-fit behavior
