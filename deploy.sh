#!/usr/bin/env bash

################################################################################
# AUTOMATED DEPLOYMENT SCRIPT
# Purpose: Automate Git cleanup, branch merge, and deployment to main
# Usage: ./deploy.sh
################################################################################

# Exit immediately if a command exits with a non-zero status
set -e

# Color codes for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
FEATURE_BRANCH="slack-ci-test"
MAIN_BRANCH="main"

################################################################################
# HELPER FUNCTIONS
################################################################################

print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Get current branch name
get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

# Check if branch exists locally
branch_exists() {
    git show-ref --verify --quiet refs/heads/"$1"
}

# Check if branch exists on remote
remote_branch_exists() {
    git ls-remote --heads origin "$1" | grep -q "$1"
}

################################################################################
# MAIN DEPLOYMENT SCRIPT
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "  🚀 AUTOMATED DEPLOYMENT SCRIPT"
echo "  Feature Branch: $FEATURE_BRANCH → Main Branch: $MAIN_BRANCH"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Step 1: Clean up .DS_Store files
################################################################################
print_step "Step 1: Cleaning up macOS .DS_Store files..."

# Check if .DS_Store is already in .gitignore
if grep -q "^\.DS_Store$" .gitignore 2>/dev/null; then
    print_success ".DS_Store already in .gitignore"
else
    print_warning "Adding .DS_Store to .gitignore"
    echo "" >> .gitignore
    echo "# macOS system files" >> .gitignore
    echo ".DS_Store" >> .gitignore
fi

# Remove all .DS_Store files from Git tracking (if any exist)
print_step "Removing .DS_Store files from Git tracking..."
if git ls-files | grep -q "\.DS_Store$"; then
    find . -name ".DS_Store" -print0 | xargs -0 git rm --cached 2>/dev/null || true
    print_success "Removed .DS_Store files from tracking"
    
    # Commit the cleanup
    git add .gitignore
    if git diff --cached --quiet; then
        print_success "No .DS_Store changes to commit"
    else
        git commit -m "chore: remove .DS_Store files from Git tracking"
        print_success "Committed .DS_Store cleanup"
    fi
else
    print_success "No .DS_Store files in Git tracking"
fi

# Step 2: Stash any uncommitted changes
################################################################################
print_step "Step 2: Checking for uncommitted changes..."

STASH_NEEDED=false
if ! git diff-index --quiet HEAD --; then
    print_warning "Uncommitted changes detected. Stashing them..."
    git stash push -m "Auto-stash before deployment at $(date)"
    STASH_NEEDED=true
    print_success "Changes stashed successfully"
else
    print_success "Working directory is clean"
fi

# Step 3: Fetch latest changes from remote
################################################################################
print_step "Step 3: Fetching latest changes from remote..."
git fetch origin
print_success "Fetched latest changes"

# Step 4: Ensure feature branch exists and is up-to-date
################################################################################
print_step "Step 4: Preparing feature branch '$FEATURE_BRANCH'..."

# Check if we're already on the feature branch
CURRENT_BRANCH=$(get_current_branch)
if [ "$CURRENT_BRANCH" != "$FEATURE_BRANCH" ]; then
    if branch_exists "$FEATURE_BRANCH"; then
        print_step "Switching to existing branch '$FEATURE_BRANCH'..."
        git checkout "$FEATURE_BRANCH"
    else
        print_error "Feature branch '$FEATURE_BRANCH' does not exist locally!"
        
        # Check if it exists on remote
        if remote_branch_exists "$FEATURE_BRANCH"; then
            print_step "Feature branch exists on remote. Checking it out..."
            git checkout -b "$FEATURE_BRANCH" origin/"$FEATURE_BRANCH"
        else
            print_error "Feature branch '$FEATURE_BRANCH' does not exist on remote either!"
            exit 1
        fi
    fi
fi

# Set upstream tracking if not set
if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} &>/dev/null; then
    print_warning "Setting upstream tracking for '$FEATURE_BRANCH'..."
    git branch --set-upstream-to=origin/"$FEATURE_BRANCH" "$FEATURE_BRANCH"
    print_success "Upstream tracking configured"
fi

# Pull latest changes
print_step "Pulling latest changes for '$FEATURE_BRANCH'..."
git pull origin "$FEATURE_BRANCH"
print_success "Feature branch is up-to-date"

# Push any local commits
print_step "Pushing feature branch to remote..."
if git push origin "$FEATURE_BRANCH"; then
    print_success "Feature branch pushed successfully"
else
    print_warning "Push failed or nothing to push"
fi

# Step 5: Switch to main branch
################################################################################
print_step "Step 5: Preparing main branch '$MAIN_BRANCH'..."

# Check if main branch exists locally
if branch_exists "$MAIN_BRANCH"; then
    print_step "Switching to existing branch '$MAIN_BRANCH'..."
    git checkout "$MAIN_BRANCH"
else
    print_warning "Main branch '$MAIN_BRANCH' does not exist locally!"
    
    # Check if it exists on remote
    if remote_branch_exists "$MAIN_BRANCH"; then
        print_step "Main branch exists on remote. Checking it out..."
        git checkout -b "$MAIN_BRANCH" origin/"$MAIN_BRANCH"
    else
        print_error "Main branch '$MAIN_BRANCH' does not exist on remote either!"
        print_error "Cannot proceed with deployment."
        exit 1
    fi
fi

# Set upstream tracking if not set
if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} &>/dev/null; then
    print_warning "Setting upstream tracking for '$MAIN_BRANCH'..."
    git branch --set-upstream-to=origin/"$MAIN_BRANCH" "$MAIN_BRANCH"
    print_success "Upstream tracking configured"
fi

# Pull latest changes
print_step "Pulling latest changes for '$MAIN_BRANCH'..."
git pull origin "$MAIN_BRANCH"
print_success "Main branch is up-to-date"

# Step 6: Merge feature branch into main
################################################################################
print_step "Step 6: Merging '$FEATURE_BRANCH' into '$MAIN_BRANCH'..."

# Check if there are any changes to merge
if git merge-base --is-ancestor "$FEATURE_BRANCH" "$MAIN_BRANCH"; then
    print_warning "Feature branch is already merged into main. Nothing to merge."
else
    print_step "Performing merge with --no-ff strategy..."
    git merge "$FEATURE_BRANCH" --no-ff -m "Merge branch '$FEATURE_BRANCH' into '$MAIN_BRANCH'

This merge includes:
- CI/CD pipeline improvements
- Slack notification integration
- Dashboard enhancements
- Bug fixes and optimizations

Deployed: $(date '+%Y-%m-%d %H:%M:%S')"
    
    print_success "Merge completed successfully"
fi

# Step 7: Push main branch to remote
################################################################################
print_step "Step 7: Pushing '$MAIN_BRANCH' to remote..."
git push origin "$MAIN_BRANCH"
print_success "Main branch deployed to remote"

# Step 8: Restore stashed changes (if any)
################################################################################
if [ "$STASH_NEEDED" = true ]; then
    print_step "Step 8: Restoring stashed changes..."
    
    # Switch back to feature branch before applying stash
    git checkout "$FEATURE_BRANCH"
    
    if git stash pop; then
        print_success "Stashed changes restored successfully"
    else
        print_warning "Stash pop failed. Your stash is preserved. Run 'git stash pop' manually."
    fi
fi

# Step 9: Summary
################################################################################
echo ""
echo "════════════════════════════════════════════════════════════════════════"
print_success "🎉 DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "  ✓ .DS_Store files cleaned and ignored"
echo "  ✓ Feature branch '$FEATURE_BRANCH' synchronized"
echo "  ✓ Changes merged into '$MAIN_BRANCH'"
echo "  ✓ Deployment pushed to GitHub"
echo ""
echo "  🔔 GitHub Actions should now be triggered on '$MAIN_BRANCH'"
echo "  🔗 Check your CI/CD dashboard for pipeline status"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Return to feature branch for continued development
if [ "$(get_current_branch)" != "$FEATURE_BRANCH" ]; then
    print_step "Switching back to '$FEATURE_BRANCH' for continued development..."
    git checkout "$FEATURE_BRANCH"
fi

exit 0



