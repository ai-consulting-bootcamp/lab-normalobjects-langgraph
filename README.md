# Chaos agent: tools, lore, less questionable judgments

**Track:** Module 3 — RAG, LangChain, agents · **When:** Week 5, Day 1 · **Status:** Required

This repository contains everything you need for this lab.

## Files

- [`instructions.md`](./instructions.md) — the lab instructions
- [`rubric.md`](./rubric.md) — how your submission is graded; this is what the AI reviewer checks your PR against

## How to complete this lab

1. **Fork** this repository.
2. Do the work described in `instructions.md`, committing to your fork.
3. Open a **pull request** back into this repository.
4. You'll receive **AI feedback** on your PR based on `rubric.md`. Address any blocking feedback and push updates to the same PR.

## Submission hygiene

- Keep this repository scoped to this lab only — no unrelated projects or personal files.
- Use clear, descriptive filenames.
- Remove secrets, API keys, and tokens before committing.

## Running the Completed Lab

The completed implementation is available in
`Lab_normalobjects_langgraph.ipynb`.

### Requirements

- Python 3
- Jupyter Notebook or VS Code with Jupyter support
- An OpenAI API key
- Python packages: `langgraph`, `langchain-openai`, `python-dotenv`

### Setup

1. Install the required Python packages:

   ```bash
   pip install langgraph langchain-openai python-dotenv ipykernel
   ```

2. Create a `.env` file in the project folder and add:

   ```text
   OPENAI_API_KEY=your_api_key_here
   ```

3. Open `Lab_normalobjects_langgraph.ipynb` in VS Code or Jupyter.

4. Select the appropriate Python environment and run the notebook cells in order.

### Expected Results

The notebook tests five complaints:

- Four valid complaints should follow:
  `intake → validate → investigate → resolve → close`
- One invalid complaint should follow:
  `intake → validate → reject`

The exact LLM-generated wording may vary.

### Review Evidence

Start with `lab_proof.md` for the workflow explanation,
test evidence, final output, traceability, limitations,
and comparison with a direct LLM call.
