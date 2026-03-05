# Pipeline Decision

## Decision Goal

We need a pipeline that reliably transforms unstructured process descriptions into high-quality interactive diagrams with error control.

## Evaluated Options

1. `Single-shot LLM`
- Pro: fast to start.
- Con: weak control and repeatability for complex processes.

2. `RAG + single-agent`
- Pro: better context.
- Con: poor separation of logic stages (decomposition, linking, QA).

3. `Multi-agent orchestration` (selected)
- Pro: each step is isolated and testable.
- Pro: easy to add validations and human review.
- Con: higher integration complexity.

## Selected Pipeline

1. `Input`  
Text/document upload.

2. `Preprocess`  
Cleaning, OCR (if needed), terminology normalization.

3. `Semantic Parse`  
Extraction of stages, entities, roles, and artifacts.

4. `Process Decomposition`  
Build L1/L2/L3 structure.

5. `Component Linking`  
Link systems and data to steps.

6. `Graph Build`  
Generate `ProcessGraph JSON`.

7. `QA + Human Gate`  
Automated checks + manual approval.

8. `Publish`  
Render in UI, export, and share.

## Pipeline Quality Criteria

- Completeness: key-stage coverage >= 90%.
- Connectivity: no unexplained dangling nodes.
- Terminology consistency: unified naming of entities.
- Reproducibility: same input -> structurally similar graph.
