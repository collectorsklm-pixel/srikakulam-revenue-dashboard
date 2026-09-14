# Putting it on GitHub Pages

## The quick way

1. Unzip `github_pages_site.zip` into the repository — `index.html`, `data/` and `.nojekyll`
   at the root (or inside `docs/` if you prefer).
2. Settings → Pages → Source: *Deploy from a branch*, pick the branch and the folder.
3. The dashboard comes up at `https://<user-or-org>.github.io/<repo>/`.

`.nojekyll` matters: without it GitHub's Jekyll step can skip the `data/` folder.

Daily, on your machine:

    python extract_snapshot.py "Revenue_Subjects_Reports_as_on_12_09_26.pdf" data
    python build.py data site
    # copy site/index.html and site/data/ into the repo, commit, push

## The hands-off way

Put `publish.yml` in `.github/workflows/`, and keep `template.html`, `build.py` and
`extract_snapshot.py` in the repository. Then the whole daily job is:

    commit the day's PDF into  packs/

GitHub installs pdfplumber, reads every pack in `packs/`, rebuilds the dashboard and publishes
it. Nothing to run locally, no Python on your laptop.

Settings → Pages → Source must be set to *GitHub Actions* for this route.

## One thing to know about the link

A Pages site on a public repository is reachable by anyone who has the address — it is not
restricted to the department, it is just unadvertised. The case lists carry applicant names,
villages and phone numbers, and with the Actions route the source PDFs sit in the repo too.

Two ways to tighten it, whenever you want:

- Make the repository private. Pages from a private repository needs GitHub Pro, Team or
  Enterprise; the site can then be limited to organisation members.
- Build without the personal columns:

      python build.py data site --no-mobile     # drops phone numbers
      python build.py data site --public        # drops names, villages, phone numbers, remarks

  Counts, ageing, oldest-case days, officer levels, application numbers and mandals all stay,
  so the review still works.
