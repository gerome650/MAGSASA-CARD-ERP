#!/bin/bash

# 🚀 GitOps Release Automation Script with Semantic Versioning
# MAGSASA-CARD-ERP DevOps Pipeline
# 
# This script provides complete automation for:
# - Staging and committing observability changes
# - Semantic version detection based on conventional commits
# - Automated tagging and GitHub release creation
# - CHANGELOG.md generation and maintenance

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_NAME="$(basename "$0")"
REPO_ROOT="$(git rev-parse --show-toplevel)"
FEATURE_BRANCH="feature/observability-intelligence"
DEFAULT_VERSION="v1.0.0"

# Flags
CI_MODE=false
AUTO_MODE=false
VERBOSE=false
DRY_RUN=false

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🧩 $1${NC}"
}

print_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

# Show usage information
show_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

GitOps Release Automation with Semantic Versioning

OPTIONS:
    --ci              Run in CI mode (skip confirmations)
    --auto            Auto-generate version without user input
    --verbose         Enable verbose output
    --dry-run         Compute next version without tagging/pushing/changelog
    --help            Show this help message

EXAMPLES:
    $SCRIPT_NAME                    # Interactive mode
    $SCRIPT_NAME --ci --auto        # CI mode with auto-versioning
    $SCRIPT_NAME --verbose          # Verbose output
    $SCRIPT_NAME --dry-run          # Show next version without creating release

DESCRIPTION:
    This script automates the complete release process:
    1. Stages and commits Stage 6.7 → 6.8.1 changes
    2. Creates feature branch if needed
    3. Detects semantic version based on conventional commits
    4. Tags the release
    5. Generates and commits CHANGELOG.md
    6. Publishes GitHub Release

SEMANTIC VERSIONING:
    - BREAKING CHANGE or ! in commit → major bump
    - feat: commits → minor bump
    - fix:, chore:, refactor:, perf:, etc. → patch bump

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --ci)
                CI_MODE=true
                shift
                ;;
            --auto)
                AUTO_MODE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Pre-flight checks
preflight_checks() {
    print_header "Pre-flight Checks"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository!"
        exit 1
    fi
    
    # Check if we're on a detached HEAD
    if git symbolic-ref -q HEAD > /dev/null 2>&1; then
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        print_info "Current branch: $CURRENT_BRANCH"
    else
        print_error "Cannot run on detached HEAD!"
        exit 1
    fi
    
    # Check if working tree is clean
    if git diff-index --quiet HEAD --; then
        print_warning "Working tree is clean - no changes to commit"
    else
        print_info "Working tree has changes to commit"
    fi
    
    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI (gh) not found. GitHub releases will be skipped."
        print_info "Install with: brew install gh (macOS) or apt install gh (Ubuntu)"
    else
        print_success "GitHub CLI found"
    fi
    
    print_success "Pre-flight checks passed"
}

# Get user confirmation
get_user_confirmation() {
    if [[ "$CI_MODE" == true || "$DRY_RUN" == true ]]; then
        print_info "CI mode or dry-run enabled - skipping user confirmation"
        return 0
    fi
    
    echo
    print_warning "Are you sure you want to commit and push all observability changes?"
    read -p "This will stage, commit, tag, and create a GitHub release. Continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Operation cancelled by user"
        exit 0
    fi
    
    print_success "User confirmed - proceeding with release"
}

# Stage and commit changes
stage_and_commit() {
    print_header "Staging and Committing Changes"
    
    # Check if there are any changes to stage
    if git diff --cached --quiet && git diff --quiet; then
        print_warning "No changes to stage or commit"
        return 0
    fi
    
    # Stage all changes
    print_step "Staging all changes..."
    git add .
    print_success "Changes staged"
    
    # Create commit with descriptive message
    COMMIT_MSG="feat: Stage 6.7-6.8.1 - Complete Observability & Intelligence Pipeline

- Stage 6.7: Advanced observability with metrics, logging, and tracing
- Stage 6.8: Runtime intelligence and automated insights
- Stage 6.8.1: AI agent integration and decision automation

This commit includes:
✅ Observability stack (Prometheus, Grafana, Jaeger)
✅ Automated alerting and remediation rules
✅ Runtime intelligence collection
✅ AI agent decision automation
✅ Complete DevOps pipeline integration

Closes: Stage 6.7, Stage 6.8, Stage 6.8.1"

    print_step "Committing changes..."
    git commit -m "$COMMIT_MSG"
    print_success "Changes committed"
}

# Handle branch creation and switching
handle_branch() {
    print_header "Branch Management"
    
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # If on main or master, create feature branch
    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        print_step "On main branch - creating feature branch: $FEATURE_BRANCH"
        git checkout -b "$FEATURE_BRANCH"
        print_success "Created and switched to feature branch"
    else
        print_info "Already on feature branch: $CURRENT_BRANCH"
    fi
    
    # Push branch to remote
    print_step "Pushing branch to remote..."
    git push -u origin "$(git rev-parse --abbrev-ref HEAD)"
    print_success "Branch pushed to remote"
}

# Get the last tag
get_last_tag() {
    local last_tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    
    if [[ -z "$last_tag" ]]; then
        echo "$DEFAULT_VERSION"
    else
        echo "$last_tag"
    fi
}

# Parse semantic version components
parse_version() {
    local version="$1"
    
    # Sanitize the tag before parsing - strip leading 'v'
    local clean_tag=${version#v}
    
    # Split into major.minor.patch
    IFS='.' read -r major minor patch <<< "$clean_tag"
    
    # Safety checks - if parsing fails (empty variables), exit gracefully
    if [[ -z "$major" || -z "$minor" || -z "$patch" ]]; then
        print_error "Failed to parse semantic version from tag: $version"
        print_error "Expected format: vMAJOR.MINOR.PATCH (e.g., v1.0.0)"
        exit 1
    fi
    
    echo "$major $minor $patch"
}

# Get commits since last tag
get_commits_since_tag() {
    local last_tag="$1"
    local commits
    
    if [[ "$last_tag" == "$DEFAULT_VERSION" ]]; then
        # If no previous tag, get all commits
        commits=$(git log --pretty=format:"%s" --reverse)
    else
        # Get commits since last tag - FIXED: commit range comes before --pretty flag
        commits=$(git log $last_tag..HEAD --pretty=format:"%s")
    fi
    
    echo "$commits"
}

# Determine version bump type
determine_bump_type() {
    local commits="$1"
    local bump_type="patch"  # Default to patch
    
    # Ensure $COMMITS is not empty - if it is, default to patch bump
    if [[ -z "$commits" ]]; then
        echo "patch"
        return 0
    fi
    
    while IFS= read -r commit; do
        if [[ -z "$commit" ]]; then
            continue
        fi
        
        # Check for breaking changes
        if [[ "$commit" =~ (BREAKING CHANGE|!.*:) ]]; then
            bump_type="major"
            break
        fi
        
        # Check for features
        if [[ "$commit" =~ ^feat: ]]; then
            if [[ "$bump_type" != "major" ]]; then
                bump_type="minor"
            fi
        fi
        
        # Other types (fix:, chore:, refactor:, perf:, etc.) are patch by default
    done <<< "$commits"
    
    echo "$bump_type"
}

# Calculate next version
calculate_next_version() {
    local last_tag="$1"
    local bump_type="$2"
    
    read -r major minor patch <<< "$(parse_version "$last_tag")"
    
    case "$bump_type" in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid bump type: $bump_type"
            exit 1
            ;;
    esac
    
    echo "v$major.$minor.$patch"
}

# Get user confirmation for version (if not in auto mode)
confirm_version() {
    local proposed_version="$1"
    local bump_type="$2"
    
    if [[ "$AUTO_MODE" == true || "$CI_MODE" == true || "$DRY_RUN" == true ]]; then
        echo "$proposed_version"
        return 0
    fi
    
    echo
    print_info "Proposed next version: $proposed_version (bump type: $bump_type)"
    read -p "Accept this version? (Y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        read -p "Enter custom version (e.g., v6.9.0): " custom_version
        echo "$custom_version"
    else
        echo "$proposed_version"
    fi
}

# Create and push tag
create_and_push_tag() {
    local version="$1"
    
    print_header "Tagging Release"
    
    # Create annotated tag
    print_step "Creating annotated tag: $version"
    git tag -a "$version" -m "Release $version: Automated semantic release
    
This release includes:
- Complete observability pipeline (Stage 6.7)
- Runtime intelligence automation (Stage 6.8)  
- AI agent decision integration (Stage 6.8.1)

Generated by GitOps automation pipeline."
    
    # Push tag to remote
    print_step "Pushing tag to remote..."
    git push origin "$version"
    
    print_success "Tag $version created and pushed"
}

# Generate CHANGELOG.md entry
generate_changelog_entry() {
    local version="$1"
    local last_tag="$2"
    local date=$(date +"%Y-%m-%d")
    
    # Get commits for this version
    local commits
    if [[ "$last_tag" == "$DEFAULT_VERSION" ]]; then
        commits=$(git log --pretty=format:"- %s" --reverse)
    else
        commits=$(git log $last_tag..HEAD --pretty=format:"- %s")
    fi
    
    # Categorize commits
    local features=""
    local fixes=""
    local breaking=""
    local other=""
    
    while IFS= read -r commit; do
        if [[ -z "$commit" ]]; then
            continue
        fi
        
        if [[ "$commit" =~ BREAKING[[:space:]]CHANGE ]] || [[ "$commit" =~ ! ]]; then
            breaking="$breaking$commit"$'\n'
        elif [[ "$commit" =~ ^-.*feat: ]]; then
            features="$features$commit"$'\n'
        elif [[ "$commit" =~ ^-.*fix: ]]; then
            fixes="$fixes$commit"$'\n'
        else
            other="$other$commit"$'\n'
        fi
    done <<< "$commits"
    
    # Generate changelog entry
    cat << EOF

## [$version] - $date

EOF

    if [[ -n "$breaking" ]]; then
        echo "### BREAKING CHANGES"
        echo "$breaking"
    fi
    
    if [[ -n "$features" ]]; then
        echo "### Added"
        echo "$features"
    fi
    
    if [[ -n "$fixes" ]]; then
        echo "### Fixed"
        echo "$fixes"
    fi
    
    if [[ -n "$other" ]]; then
        echo "### Changed"
        echo "$other"
    fi
}

# Update CHANGELOG.md
update_changelog() {
    local version="$1"
    local last_tag="$2"
    
    print_header "Updating CHANGELOG.md"
    
    # Create temporary file for new changelog
    local temp_changelog=$(mktemp)
    
    # Add header to temp file
    cat > "$temp_changelog" << 'EOF'
# Changelog

All notable changes to the MAGSASA-CARD ERP system will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF

    # Generate new version entry
    generate_changelog_entry "$version" "$last_tag" >> "$temp_changelog"
    
    # Append existing changelog (skip header)
    if [[ -f "$REPO_ROOT/CHANGELOG.md" ]]; then
        tail -n +8 "$REPO_ROOT/CHANGELOG.md" >> "$temp_changelog"
    fi
    
    # Replace original changelog
    mv "$temp_changelog" "$REPO_ROOT/CHANGELOG.md"
    
    print_success "CHANGELOG.md updated"
}

# Commit and push CHANGELOG.md
commit_changelog() {
    local version="$1"
    
    print_header "Committing CHANGELOG.md"
    
    git add CHANGELOG.md
    git commit -m "docs(changelog): update CHANGELOG.md for $version"
    git push origin "$(git rev-parse --abbrev-ref HEAD)"
    
    print_success "CHANGELOG.md committed and pushed"
}

# Create GitHub release
create_github_release() {
    local version="$1"
    
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI not available - skipping release creation"
        print_info "Install with: brew install gh (macOS) or apt install gh (Ubuntu)"
        return 0
    fi
    
    print_header "Creating GitHub Release"
    
    # Check if already authenticated
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI not authenticated"
        print_info "Run: gh auth login"
        return 1
    fi
    
    # Create release using CHANGELOG.md as notes
    print_step "Creating GitHub release: $version"
    
    # Extract release notes from CHANGELOG.md
    local release_notes=$(awk "/^## \[$version\]/{flag=1;next}/^## \[/{flag=0}flag" "$REPO_ROOT/CHANGELOG.md")
    
    if [[ -z "$release_notes" ]]; then
        release_notes="Release $version

This release includes the complete observability and intelligence pipeline implementation."
    fi
    
    # Create the release
    if gh release create "$version" \
        --title "$version" \
        --notes "$release_notes" \
        --latest; then
        print_success "GitHub release created: $version"
        
        # Get release URL
        local release_url=$(gh release view "$version" --json url --jq '.url')
        print_info "Release URL: $release_url"
    else
        print_error "Failed to create GitHub release"
        return 1
    fi
}

# Main execution function
main() {
    print_header "GitOps Release Automation with Semantic Versioning"
    print_info "Repository: $REPO_ROOT"
    print_info "Script: $SCRIPT_NAME"
    echo
    
    # Parse arguments
    parse_args "$@"
    
    # Run pre-flight checks
    preflight_checks
    echo
    
    # Get user confirmation
    get_user_confirmation
    echo
    
    # Stage and commit changes (skip in dry-run mode)
    if [[ "$DRY_RUN" != true ]]; then
        stage_and_commit
        echo
        
        # Handle branch management
        handle_branch
        echo
    else
        print_info "Dry-run mode - skipping staging, committing, and branch management"
    fi
    
    # Semantic versioning logic
    print_header "Semantic Version Detection"
    
    # Get last tag
    local last_tag
    last_tag=$(get_last_tag)
    
    if [[ -z "$last_tag" ]]; then
        print_info "No previous tags found, using default: $DEFAULT_VERSION"
    else
        print_info "Last tag detected: $last_tag"
    fi
    
    # Get commits since last tag
    local commits
    commits=$(get_commits_since_tag "$last_tag")
    
    if [[ "$VERBOSE" == true ]]; then
        print_info "Commits since $last_tag:"
        echo "$commits" | sed 's/^/  /'
        echo
    fi
    
    # Determine bump type
    local bump_type
    bump_type=$(determine_bump_type "$commits")
    
    if [[ -z "$commits" ]]; then
        print_info "No commits found since last tag - defaulting to patch bump"
    fi
    print_info "Detected bump type: $bump_type"
    
    # Calculate next version
    local proposed_version
    proposed_version=$(calculate_next_version "$last_tag" "$bump_type")
    print_info "Proposed next version: $proposed_version"
    
    # Get user confirmation for version
    local final_version
    final_version=$(confirm_version "$proposed_version" "$bump_type")
    
    print_success "Final version: $final_version"
    echo
    
    # Handle dry-run mode
    if [[ "$DRY_RUN" == true ]]; then
        print_header "DRY RUN MODE - No changes will be made"
        print_info "Would create tag: $final_version"
        print_info "Would update CHANGELOG.md"
        print_info "Would create GitHub release"
        echo
        print_success "Dry run complete - version would be: $final_version"
        return 0
    fi
    
    # Create and push tag
    create_and_push_tag "$final_version"
    echo
    
    # Update CHANGELOG.md
    update_changelog "$final_version" "$last_tag"
    
    # Commit changelog
    commit_changelog "$final_version"
    echo
    
    # Create GitHub release
    create_github_release "$final_version"
    echo
    
    # Final summary
    print_header "Release Complete! 🚀"
    print_success "Version: $final_version"
    print_success "Branch: $(git rev-parse --abbrev-ref HEAD)"
    print_success "Tag: $final_version"
    print_success "CHANGELOG.md: Updated"
    
    if command -v gh &> /dev/null; then
        print_success "GitHub Release: Created"
    fi
    
    echo
    print_info "Next steps:"
    print_info "1. Review the changes and release"
    print_info "2. Merge feature branch to main if ready"
    print_info "3. Monitor the deployment pipeline"
    
    print_success "GitOps automation complete! 🎉"
}

# Run main function with all arguments (only if not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
