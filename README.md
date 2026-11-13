# sizewise

**Find out what is actually eating your disk.** Read-only: it walks a folder and prints a
summary. It never deletes, moves or modifies anything.

```
sizewise 1.0 - tree

  345.7 KB in 3 file(s), 2 folder(s)

  Largest entries
     293.0 KB   84.7%  #####################      videos
      43.9 KB   12.7%  ###                        docs
       8.8 KB    2.5%  #                          (files in root)

  Largest files
     293.0 KB  tree/videos/clip.mp4
      43.9 KB  tree/docs/report.pdf
       8.8 KB  tree/notes.txt
```

## Quick start

```bash
python sizewise.py                    # current folder
python sizewise.py ~/Downloads        # any folder
python sizewise.py --top 20           # more entries
python sizewise.py --files            # files only, skip the folder rollup
python sizewise.py --json             # machine-readable, for scripts
```

## What it reports

- Total bytes, file count and folder count
- **Largest entries** — every top-level child with its full recursive size and share of the
  total, with a bar you can read at a glance
- **Largest files** — the individual files doing the damage

The folder rollup is the useful part: `~/Downloads` being 40 GB tells you nothing, but
`videos 84.7%` tells you where to look.

## Details

- **Symlinks are not followed**, so it cannot loop or double-count a link farm.
- **Unreadable files are skipped**, not fatal — it runs fine on folders with permission
  oddities.
- **One pass.** It walks the tree once and aggregates as it goes, rather than stat-ing the
  same subtree repeatedly.
- **`--json` is stable** enough to pipe into `jq`.

## Tests

```bash
python tests/test_sizewise.py      # 10 tests
```

Totals, file sorting, directory rollup arithmetic, empty folders, symlink handling, unit
formatting, JSON output, and the exit codes for a missing path and a file-instead-of-folder.

## Licence

MIT with Commons Clause. Copyright (c) 2026 Siddhant Neekhra. See [LICENSE.md](LICENSE.md).
