# Submission Checklist

Target path:

1. arXiv preprint.
2. Elsevier Software Impacts submission.
3. PeerJ Computer Science as a stretch target after the paper is strengthened.

Official links:

- arXiv submit help: https://arxiv.org/help/submit
- arXiv TeX submission help: https://info.arxiv.org/help/submit_tex.html
- arXiv preparation help: https://info.arxiv.org/help/prep.html
- Software Impacts Guide for Authors: https://www.elsevier.com/journals/software-impacts/2665-9638/guide-for-authors
- Software Impacts article template PDF: https://legacyfileshare.elsevier.com/promis_misc/SIMPAC_Article_Template.pdf

Downloaded local templates:

- `submission_materials/official_templates/software_impacts_article_template.tex`
- `submission_materials/official_templates/Software_Template.docx`
- `submission_materials/official_templates/SIMPAC_Article_Template.pdf`

## arXiv Checklist

Recommended category:

- Primary: `cs.SE` for software engineering.
- Optional secondary: `cs.AI` if the final abstract emphasizes LLM evaluation.

Before upload:

- Compile `paper/main.tex` locally.
- If local LaTeX is unavailable, follow `submission_materials/PDF_BUILD_GUIDE.md`
  and compile the arXiv package in Overleaf.
- Copy figures into the paper folder or update figure paths so arXiv can find them.
- Include `paper/main.tex`, `paper/references.bib`, and all referenced figure files.
- Remove local machine paths.
- Remove secrets: no `.env`, no API keys, no private logs.
- Decide license for the arXiv paper.
- Make sure the abstract states this is a reproducible pilot if human validation is not complete.
- Do not claim human inter-rater agreement unless human review has actually been completed.

Suggested arXiv source package contents:

```text
main.tex
references.bib
fig1_category_freq.png
fig2_category_by_model.png
fig3_logic_subcat.png
```

## Software Impacts Checklist

Software Impacts is a software-article venue. The submission should emphasize the
research software artifact, not only the empirical result.

Important fit risk:

- The official guide says Software Impacts considers freely available software under
  a recognized legal license, and describes software that has contributed to
  scientific research. It also says the software article format is different from a
  traditional research article and that the journal only considers submissions using
  its template. Treat this as a software-artifact submission, not a normal empirical
  paper submission.
- If the editors require prior peer-reviewed published results, an arXiv-only
  preprint may be weaker than a PeerJ/other reviewed paper. In that case, keep PeerJ
  Computer Science or another reviewed venue as the research-paper route, then use
  Software Impacts for the software artifact.

Required or strongly expected materials:

- Manuscript in the Software Impacts template.
- PDF built from `paper/software_impacts.tex` locally or in Overleaf.
- Public source-code repository.
- Open-source license, such as MIT or Apache-2.0.
- Archived software release with DOI, such as Zenodo.
- Clear installation and reproduction instructions.
- Software metadata table.
- Data availability statement.
- Conflict of interest statement.
- Funding statement, even if it says no external funding.
- CRediT author contribution statement.
- Highlights, if requested by Editorial Manager.

Drafted submission statements:

- `submission_materials/SUBMISSION_STATEMENTS.md`

Software artifact readiness:

- Repository has `README.md`.
- Repository has `requirements.txt` or equivalent environment file.
- Repository has `LICENSE`.
- Repository has `CITATION.cff`.
- Scripts run in the order documented in `README.md`.
- Generated labels/results needed for reproducibility are included or linked.
- API keys are never committed.
- The exact model identifiers and access date are documented.

Current agreement status:

- `python src/second_annotator.py` has produced 96/96 blind second labels.
- `python src/kappa.py` reports exact agreement 42/96 (43.8%) and Cohen's kappa 0.305.
- The manuscript now reports this as fair automatic agreement and treats subtype labels cautiously.
- Keep human validation as a limitation unless actually completed.

## PeerJ Computer Science Stretch Checklist

PeerJ Computer Science is a more research-oriented target. Before aiming there:

- Add MBPP or another benchmark.
- Add multiple samples per problem.
- Add human validation or at least a carefully designed human audit.
- Strengthen related work and novelty against Tambon et al. 2024 and other LLM-code-bug studies.
- Add effect sizes and confidence intervals where appropriate.
