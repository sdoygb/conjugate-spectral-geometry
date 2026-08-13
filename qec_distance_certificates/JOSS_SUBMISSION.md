# JOSS Submission Guide

## Pre-submission checklist (all verified 2026-08-13)

- [x] Software has an **OSI-approved license** (MIT, `LICENSE` file)
- [x] Software is hosted in a **public repository** (https://github.com/sdoygb/qec-distance-certificates)
- [x] Repository has a **version tag** (`v0.1.0`)
- [x] **Tests** present and passing (`pytest`, 15 tests)
- [x] **Documentation**: README with install instructions, API, and benchmark table
- [x] **paper.md** and **paper.bib** in `paper/` (JOSS template format)
- [x] **Contributors** listed as authors (paper.md front matter)
- [ ] **PyPI release** (recommended, not required by JOSS): build artifacts
      (`dist/qec_distance_certificates-0.1.0.tar.gz`, `...-py3-none-any.whl`)
      have passed `twine check`; upload with `twine upload dist/*`
      (needs a PyPI API token), or manually at https://pypi.org/manage/projects/

## Submission steps

1. Go to https://github.com/openjournals/joss-reviews/issues
2. Click **New Issue** and select the **Software Submission** template
3. Fill the template fields:
   - Submitting author: `@sdoygb` (Guobin Ouyang)
   - Repository: `https://github.com/sdoygb/qec-distance-certificates`
   - Version: `v0.1.0`
   - Branch: `main` (paper at `paper/paper.md`)
   - Editor: leave suggested editor blank (or follow template)
   - Software license: MIT
4. Copy the checklist below into the issue body and tick items as true:

```
Submitting author: @sdoygb (Guobin Ouyang)
Repository link: https://github.com/sdoygb/qec-distance-certificates
Version: v0.1.0
Branch containing the paper: main (paper at paper/paper.md)
Editor: Pending
Reviewers: Pending
Archive: Pending
```

## Post-submission

- A JOSS editor will run the pre-submission checks and either assign a
  reviewer or request changes (checklist items marked false).
- Review is public; expect 2-3 months from submission to acceptance for
  software in good shape.
- The Zoo PR (#381, errorcorrectionzoo/eczoo_data) is independent and can
  be cross-linked from the JOSS issue once merged.
