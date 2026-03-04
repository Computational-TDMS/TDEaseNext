# Design Token System

## Purpose

Establishes a global CSS custom property (variable) design system for the workflow editor frontend. Provides a single source of truth for colors, typography, spacing, borders, and shadows, replacing scattered hard-coded values across component files.

## Requirements

### Requirement: CSS variable design tokens
The system SHALL define all UI primitives as CSS custom properties in a single `src/assets/design-tokens.css` file, imported globally via `main.ts`.

#### Scenario: Token file is loaded before any component styles
- **WHEN** the Vue app initializes
- **THEN** all CSS custom properties defined in `design-tokens.css` SHALL be available to all components
- **AND** component styles SHALL reference tokens via `var(--token-name)` instead of hard-coded values

#### Scenario: Node type colors expressed as tokens
- **WHEN** a node is rendered in the canvas
- **THEN** its accent color SHALL be determined by `--node-tool`, `--node-interactive`, `--node-input`, or `--node-output` tokens respectively
- **AND** the token value SHALL be applied as a `border-left: 4px solid var(--node-color)` on the node card

### Requirement: Node card visual standard
The system SHALL define a visual standard for all node cards (ToolNode, InteractiveNode) that replaces the current full-perimeter colored border.

#### Scenario: Tool node renders with standard card style
- **WHEN** a tool node is displayed in the workflow canvas
- **THEN** it SHALL show: white background, `border-radius: 12px`, `border: 1px solid var(--border-subtle)`, `border-left: 4px solid var(--node-color)`, and a light diffuse shadow
- **AND** on hover, the shadow SHALL intensify and the card SHALL translate upward by 1px

#### Scenario: Interactive node distinguishable from tool node
- **WHEN** an interactive visualization node is displayed
- **THEN** its `--node-color` SHALL be `var(--node-interactive)` (purple `#8B5CF6`)
- **AND** it SHALL be visually distinguishable from tool nodes without requiring a text label
