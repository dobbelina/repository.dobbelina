# Keeping Pull Requests in Your Fork

If you're working from a fork of this repository and want to be certain that
branches, pushes, and pull requests stay in **your** namespace, follow the
steps below.

## 1. Confirm your remotes

List the configured git remotes and confirm that `origin` points at your fork:

```bash
git remote -v
```

If you see an `upstream` remote, that's fine—just make sure you do **not**
push to it. You can remove it altogether if you never plan to submit changes
back to the original project:

```bash
git remote remove upstream
```

## 2. Push branches to `origin`

Create and publish topic branches directly to your fork:

```bash
git checkout -b my-feature
# ...work...
git push -u origin my-feature
```

The `-u` flag records `origin/my-feature` as the default upstream branch so
future pushes can simply use `git push`.

## 3. Open PRs against your fork

When GitHub offers the **Compare & pull request** prompt, double-check that the
"base repository" dropdown is set to your fork. If it points to the original
project, change it before creating the PR. You can also create the PR manually
by visiting:

```
https://github.com/<your-user>/repository.dobbelina/compare
```

…replacing `<your-user>` with your GitHub username.

## 4. (Optional) Protect the upstream remote

If you keep the upstream remote for syncing purposes, you can make it
fetch-only so accidental pushes fail immediately:

```bash
git remote set-url --push upstream no_push
```

This leaves pull operations untouched while preventing any push attempts from
succeeding.

Following these steps guarantees that every branch and pull request you create
stays within your fork until you're ready to contribute upstream.
