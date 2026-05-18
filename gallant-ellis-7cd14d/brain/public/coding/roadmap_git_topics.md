# Git & GitHub Roadmap — Topic Index + Quick Reference

> Sumber: roadmap.sh/git-github (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/git-github

## Git Fundamentals

### Core Concepts
- **Repository (repo)**: folder tracked by git; contains `.git/` directory
- **Working tree**: files you see and edit
- **Index (staging area)**: snapshot prepared for next commit
- **Commit**: permanent snapshot of staging area + metadata (author, message, parent)
- **HEAD**: pointer to current branch tip (or specific commit in detached HEAD state)
- **Blob**: file content object; **Tree**: directory structure; **Commit**: links tree + parent

### Setup
```bash
git config --global user.name "Fahmi"
git config --global user.email "fahmiwol@gmail.com"
git config --global core.editor "code --wait"
git config --global init.defaultBranch main
git config --list
```

### Repository Operations
```bash
git init                    # initialize new repo
git clone <url>             # clone remote repo
git clone --depth 1 <url>   # shallow clone (faster, just latest commit)
git clone --branch dev <url> # clone specific branch
```

## Staging and Committing

```bash
git status                  # show modified / staged files
git add file.py             # stage specific file
git add .                   # stage all changes in current dir
git add -p                  # interactive staging (chunk by chunk)
git add -u                  # stage only tracked files (no new files)

git commit -m "feat: add user auth"
git commit --amend          # modify last commit (message or content)
git commit --amend --no-edit # amend without changing message

git diff                    # unstaged changes
git diff --staged           # staged changes (vs last commit)
git diff HEAD~2             # compare with 2 commits ago
git diff branch1..branch2   # compare branches
```

## Branching

```bash
git branch                  # list local branches
git branch -a               # list all (local + remote)
git branch feature/login    # create branch
git checkout feature/login  # switch to branch
git switch feature/login    # modern equivalent (git 2.23+)
git switch -c feature/login # create + switch (replaces checkout -b)

git branch -d feature/done  # delete merged branch
git branch -D feature/wip   # force delete unmerged branch
git branch -m old-name new-name  # rename branch

# Move branch pointer to specific commit
git branch -f main HEAD~3
```

## Merging and Rebasing

```bash
# Merge — creates merge commit preserving history
git checkout main
git merge feature/login     # merge feature into main
git merge --no-ff feature/x # always create merge commit (no fast-forward)
git merge --squash feature/x # squash into one commit (then git commit)
git merge --abort           # abort in-progress merge

# Rebase — replay commits on new base (linear history)
git checkout feature/login
git rebase main             # rebase feature onto main
git rebase -i HEAD~4        # interactive rebase: squash, edit, reorder
git rebase --abort          # abort rebase
git rebase --continue       # continue after resolving conflicts

# Rebase interactive operations (in editor):
# pick   — use commit as-is
# reword — use commit, edit message
# squash — meld into previous commit
# fixup  — meld, discard message
# drop   — remove commit
# edit   — stop here to amend
```

### Merge vs Rebase
| | Merge | Rebase |
|---|---|---|
| History | Preserves divergence (merge commit) | Linear (no merge commits) |
| Safety | Safe for shared branches | Risky on shared/public branches |
| Use case | Feature → main integration | Keep feature branch current |
| Rule | Never rebase public branch others use | Rebase local, merge public |

## Remote Operations

```bash
git remote add origin https://github.com/user/repo.git
git remote -v               # list remotes
git remote rename origin upstream
git remote remove origin

git fetch origin            # download remote changes (no merge)
git fetch --all             # fetch all remotes
git pull origin main        # fetch + merge
git pull --rebase origin main # fetch + rebase (cleaner)

git push origin main
git push -u origin main     # set upstream tracking
git push --force-with-lease  # safer force push (fails if remote advanced)
git push origin :branch-name # delete remote branch
git push origin --delete branch-name # same

git push --tags             # push tags
git push origin v1.0.0      # push specific tag
```

## Undoing Changes

```bash
# Working tree (unstaged)
git restore file.py         # discard unstaged changes to file
git checkout -- file.py     # same (older syntax)
git clean -fd               # remove untracked files and dirs

# Staged (index)
git restore --staged file.py # unstage file (keep working tree changes)
git reset HEAD file.py      # older syntax for same

# Commits (safe — doesn't change history)
git revert HEAD             # create new commit undoing HEAD
git revert HEAD~2..HEAD     # revert range of commits

# Commits (destructive — rewrites history)
git reset --soft HEAD~1     # undo commit, keep changes staged
git reset --mixed HEAD~1    # undo commit, keep changes unstaged (default)
git reset --hard HEAD~1     # undo commit, discard changes PERMANENTLY

# Reflog — recover "lost" commits
git reflog                  # log of all HEAD movements
git checkout HEAD@{3}       # jump to specific reflog entry
git reset --hard HEAD@{2}   # recover to reflog entry
```

## Stashing

```bash
git stash                   # stash current changes
git stash push -m "WIP: auth" # stash with message
git stash push --include-untracked  # include new files
git stash list              # list stashes
git stash apply             # apply latest stash (keep stash)
git stash pop               # apply + remove from stash list
git stash apply stash@{2}   # apply specific stash
git stash drop stash@{0}    # delete specific stash
git stash clear             # delete all stashes
git stash branch new-branch # create branch from stash
```

## Tags

```bash
git tag                     # list tags
git tag v1.0.0              # lightweight tag
git tag -a v1.0.0 -m "Release 1.0" # annotated tag (preferred)
git tag -a v1.0.0 abc123    # tag specific commit
git show v1.0.0             # show tag details
git push origin v1.0.0      # push single tag
git push origin --tags      # push all tags
git tag -d v1.0.0           # delete local tag
git push origin :refs/tags/v1.0.0  # delete remote tag
```

## Log and History

```bash
git log
git log --oneline           # compact one-line format
git log --oneline --graph --all  # visual branch graph
git log --author="Fahmi"
git log --since="2 weeks ago"
git log --grep="fix"        # search commit messages
git log -- file.py          # commits touching specific file
git log -p                  # show diffs in log

git show abc1234            # show specific commit
git show HEAD:file.py       # show file content at HEAD

# Pretty format
git log --pretty=format:"%h %ad %s" --date=short

# Find commit that introduced a bug
git bisect start
git bisect bad HEAD         # current commit is bad
git bisect good v1.2.0      # last known good commit
# git tests each commit, you run tests and mark good/bad
git bisect good             # or: git bisect bad
git bisect reset            # end bisect session
```

## Advanced Git

### Cherry-pick
```bash
git cherry-pick abc1234     # apply specific commit to current branch
git cherry-pick abc1234 def5678  # multiple commits
git cherry-pick A..B        # range (exclusive A)
git cherry-pick A^..B       # range (inclusive A)
git cherry-pick --no-commit abc1234  # apply changes without committing
```

### Worktrees
```bash
# Multiple working directories from one repo
git worktree add ../feature-branch feature/x
git worktree list
git worktree remove ../feature-branch
```

### Submodules
```bash
git submodule add https://github.com/user/lib.git lib
git submodule update --init --recursive
git submodule update --remote  # update to latest
```

## .gitignore

```gitignore
# Patterns
*.log           # all .log files
!important.log  # exclude from above rule
/build          # only root-level build/
dist/           # any dist/ directory
**/*.pyc        # any .pyc in any subdirectory

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
dist/

# Node
node_modules/
.env
dist/
*.min.js

# General
.DS_Store
Thumbs.db
.idea/
.vscode/
```

## GitHub Workflow

### Pull Requests
1. Fork or create branch
2. Make changes with clear commits
3. Push branch: `git push -u origin feature/x`
4. Open PR: compare & pull request on GitHub
5. Code review cycle (review, request changes, approve)
6. Merge: squash & merge / rebase & merge / merge commit
7. Delete branch after merge

### GitHub Actions CI/CD
```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
      - name: Lint
        run: ruff check .
```

### Git Flow vs GitHub Flow

**Git Flow** (complex, release-based):
- `main` — production
- `develop` — integration
- `feature/*` — new features → merge into develop
- `release/*` — release prep → merge into main + develop
- `hotfix/*` — prod fixes → merge into main + develop

**GitHub Flow** (simple, continuous delivery):
- `main` — always deployable
- `feature/xyz` → PR → review → merge to main → deploy
- Simpler; works when you deploy constantly

### Conventional Commits
```
<type>[optional scope]: <description>

feat: add user authentication
fix(api): handle null response from payment gateway
docs: update API documentation
refactor: extract auth logic to separate module
test: add unit tests for user service
chore: update dependencies
ci: add GitHub Actions workflow
perf: optimize database queries with connection pooling
breaking!: remove deprecated v1 API endpoints
```

## Git Configuration Tips

```bash
# Useful aliases
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.lg "log --oneline --graph --all"
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.wip "commit -am 'WIP'"

# Auto-correct typos
git config --global help.autocorrect 10

# Better diff with patience algorithm
git config --global diff.algorithm patience

# Always rebase on pull
git config --global pull.rebase true

# Push only current branch
git config --global push.default current
```

## Referensi Lanjut
- https://roadmap.sh/git-github
- https://git-scm.com/book (Pro Git — free online)
- https://learngitbranching.js.org/ — interactive visualization
- https://docs.github.com/en/actions
