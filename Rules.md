# Project Rules - HalfFull

This document outlines the general project guidelines and branching strategy for the HalfFull project. Adherence to these rules is mandatory for all team members to ensure a clean, traceable, and professional development process.

## Table of Contents

- [General Project Rules](#general-project-rules)
- [Git Branching Strategy](#git-branching-strategy)
    - [Main Branch](#main-branch)
    - [Supporting Branches](#supporting-branches)
        - [Feature Branches](#1-feature-branches)
        - [Release Branches](#2-release-branches)
        - [Hotfix Branches](#3-hotfix-branches)
        - [Bugfix Branches](#4-bugfix-branches)
    - [General Rules and Best Practices](#general-rules-and-best-practices)

## General Project Rules

*Add your general project rules here (e.g., code style, documentation requirements, communication guidelines, etc.)*

## Git Branching Strategy


## Main Branch

Our workflow is based on a single main branch with infinite lifetime:

*   `main`: This branch contains production-ready code. All development work is integrated here through Pull Requests. Direct commits to the `main` branch are strictly forbidden. Merges occur exclusively via Pull Requests from `feature`, `bugfix`, `release`, or `hotfix` branches. Nightly builds and automated tests run on this branch.


## Supporting Branches

We use various supporting branches for daily development. These branches have a limited lifespan.

### 1. Feature Branches

For every new function, a separate `feature` branch is created.

*   **Must branch off from:** `develop`
*   **Must merge back into:** `develop`
*   **Naming convention:** `feature/<feature-description>`
    *   **Example:** `feature/user-authentication`

**Workflow:**
1.  Create a new branch from `develop`: `git checkout -b feature/new-feature develop`
2.  Implement the feature and commit your changes.
3.  Push your branch regularly to the remote server.
4.  When the feature is finished, create a Pull Request to merge it into `develop`.

### 2. Release Branches

When the `develop` branch has reached a stable state for a release, a `release` branch is created.

*   **Must branch off from:** `develop`
*   **Must merge back into:** `main` and `develop`
*   **Naming convention:** `release/<version>`
    *   **Example:** `release/v1.2.0`

**Workflow:**
1.  Create a `release` branch from `develop`. From this point on, only bugfixes and adjustments necessary for the release are made on this branch.
2.  After completion of tests and approval, the `release` branch is merged into `main` and tagged.
3.  Important bugfixes made in the `release` branch must also be merged back into the `develop` branch.

### 3. Hotfix Branches

Hotfix branches are used to quickly fix critical errors in the production version.

*   **Must branch off from:** `main` (from a specific tag)
*   **Must merge back into:** `main` and `develop`
*   **Naming convention:** `hotfix/<short-description>` or `hotfix/<version>`
    *   **Example:** `hotfix/login-problem` or `hotfix/v1.2.1`

**Workflow:**
1.  Create a `hotfix` branch from the corresponding tag in the `main` branch.
2.  Fix the error and commit the changes.
3.  After successful tests, the `hotfix` branch is merged into `main` and `develop`. The `main` branch is tagged with a new patch version.

### 4. Bugfix Branches

For non-critical errors fixed within the normal development cycle.

*   **Must branch off from:** `develop`
*   **Must merge back into:** `develop`
*   **Naming convention:** `bugfix/<short-description>` or `bugfix/<issue-number>`
    *   **Example:** `bugfix/display-error-in-dashboard`

**Workflow:**
The workflow for `bugfix` branches is identical to that for `feature` branches.

## General Rules and Best Practices

*   **Descriptive Branch Names:** Use clear and descriptive names for your branches.
*   **Pull Requests:** All merges into `main` and `develop` must be done via a Pull Request (PR) approved by at least one other team member.
*   **Cleanup:** Delete feature, bugfix, and hotfix branches after a successful merge to keep the repository clean.
*   **Regular Syncing:** Keep your branches up to date by regularly merging or rebasing changes from the parent branch (e.g., `develop`) into your working branch.
*   **Atomic Commits:** Create small, logically coherent commits with meaningful commit messages.
