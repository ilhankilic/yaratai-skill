# Branch Protection Setup for SkillForge
# Run these commands using GitHub CLI (gh) or configure via GitHub web UI.
#
# GitHub Web UI: Settings → Branches → Add branch protection rule
#
# ═══════════════════════════════════════════════════════════════
# MASTER BRANCH (Production — public, read-only for contributors)
# ═══════════════════════════════════════════════════════════════
# Rule: master
# ✅ Require a pull request before merging
# ✅ Require approvals: 1
# ✅ Require status checks to pass before merging
#    - Required checks: "test" (from .github/workflows/test.yml)
# ✅ Require branches to be up to date before merging
# ✅ Restrict who can push to matching branches
#    - Only: ilhankilic (repo owner)
# ❌ Allow force pushes: OFF
# ❌ Allow deletions: OFF
#
# ═══════════════════════════════════════════════════════════════
# DEV BRANCH (Development — only maintainer can merge)
# ═══════════════════════════════════════════════════════════════
# Rule: dev
# ✅ Require a pull request before merging
# ✅ Require status checks to pass before merging
#    - Required checks: "test"
# ✅ Restrict who can push to matching branches
#    - Only: ilhankilic (repo owner)
# ❌ Allow force pushes: OFF
# ❌ Allow deletions: OFF
#
# ═══════════════════════════════════════════════════════════════
# DEFAULT BRANCH
# ═══════════════════════════════════════════════════════════════
# Set "master" as the default branch (what users see first on GitHub).
# Settings → General → Default branch → master
#
# This ensures:
# - `git clone` pulls master (stable, production)
# - Contributors see master first on the GitHub page
# - PRs default target to dev (configured in CONTRIBUTING.md)

