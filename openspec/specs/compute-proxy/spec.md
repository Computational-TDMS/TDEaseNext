# Compute Proxy

## Purpose

Provide backend API endpoints that interactive nodes can invoke for computationally intensive operations during user interaction. This capability enables frontend widgets to offload heavy computations (e.g., fragment ion matching, modification search) to the backend while maintaining real-time interactivity, with results integrated back into the State Bus for downstream consumption.

## Requirements

### Requirement: Compute Proxy API endpoint
The system SHALL provide backend API endpoints that interactive nodes can invoke for computationally intensive operations during user interaction.

#### Scenario: Fragment ion matching request
- **WHEN** a SpectrumNode receives a sequence string via its `state-in` port
- **AND** the node has spectrum data loaded
- **THEN** the frontend SHALL send a `POST /api/compute-proxy/fragment-match` request
- **AND** the request body SHALL include `{ sequence, spectrumData: [{mz, intensity}], ppmTolerance }`
- **AND** the response SHALL return `{ annotations: [{mz, type, error, matchedMz}] }`

#### Scenario: Modification search request
- **WHEN** a user selects peaks in a SpectrumNode and triggers modification matching
- **THEN** the frontend SHALL send a `POST /api/compute-proxy/modification-search` request
- **AND** the request body SHALL include `{ selectedPeaks: [{mz, intensity}], modificationDb, ppmTolerance }`
- **AND** the response SHALL return `{ matches: [{peakMz, modification, deltaMass, error}] }`

#### Scenario: Compute Proxy loading state
- **WHEN** a compute proxy request is in flight
- **THEN** the requesting node SHALL display a loading indicator on the affected widget
- **AND** the node SHALL remain interactive for non-affected widgets

#### Scenario: Compute Proxy error handling
- **WHEN** a compute proxy request fails (network error, server error, timeout)
- **THEN** the node SHALL display an error indicator with retry button
- **AND** the error SHALL NOT affect other nodes' state

#### Scenario: Result caching
- **WHEN** a compute proxy request has the same parameters as a previous request within 5 minutes
- **THEN** the frontend SHALL return the cached result without making a new API call
- **AND** the cache SHALL be invalidated when the underlying data changes

### Requirement: Compute Proxy backend service
The system SHALL implement backend services for compute-intensive interactive operations.

#### Scenario: FragmentMatcher service
- **WHEN** the fragment-match endpoint receives a valid request
- **THEN** the service SHALL compute theoretical b/y ion m/z values from the sequence
- **AND** match each theoretical ion against the spectrum data within PPM tolerance
- **AND** return the matched annotations with error values

#### Scenario: ModificationMatcher service
- **WHEN** the modification-search endpoint receives a valid request
- **THEN** the service SHALL look up delta masses from the modification database (Unimod or custom)
- **AND** compare each selected peak against known modifications within PPM tolerance
- **AND** return ranked matches

### Requirement: Compute Proxy integration with State Bus
The system SHALL integrate compute proxy results back into the State Bus.

#### Scenario: Annotation results dispatched to State Bus
- **WHEN** a compute proxy request completes successfully
- **THEN** the result SHALL be dispatched to the State Bus as a `state/annotation` payload
- **AND** any downstream nodes subscribing to annotation state SHALL automatically update
