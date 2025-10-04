#!/bin/bash

# 🧪 Test Script for Semantic Versioning Logic
# This script tests the semantic versioning detection without making actual changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

print_test() {
    echo -e "${CYAN}🧪 $1${NC}"
}

# Test functions from the main script
parse_version() {
    local version="$1"
    # Remove 'v' prefix if present
    version="${version#v}"
    
    # Split into major.minor.patch
    IFS='.' read -r major minor patch <<< "$version"
    
    echo "$major $minor $patch"
}

determine_bump_type() {
    local commits="$1"
    local bump_type="patch"  # Default to patch
    
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

# Test cases
test_semantic_versioning() {
    print_header "Testing Semantic Versioning Logic"
    
    # Test 1: Patch bump (fix commits)
    print_test "Test 1: Patch bump with fix commits"
    commits_fix="fix: correct log field formatting
chore: improve README
refactor: clean up code structure"
    
    bump_type=$(determine_bump_type "$commits_fix")
    next_version=$(calculate_next_version "v6.8.1" "$bump_type")
    
    print_info "Commits: $commits_fix"
    print_info "Bump type: $bump_type"
    print_info "Next version: $next_version"
    
    if [[ "$next_version" == "v6.8.2" ]]; then
        print_success "✅ Patch bump test passed"
    else
        print_error "❌ Patch bump test failed - expected v6.8.2, got $next_version"
    fi
    
    echo
    
    # Test 2: Minor bump (feat commits)
    print_test "Test 2: Minor bump with feat commits"
    commits_feat="feat: add new anomaly detection pipeline
fix: correct alert routing bug
chore: update dependencies"
    
    bump_type=$(determine_bump_type "$commits_feat")
    next_version=$(calculate_next_version "v6.8.1" "$bump_type")
    
    print_info "Commits: $commits_feat"
    print_info "Bump type: $bump_type"
    print_info "Next version: $next_version"
    
    if [[ "$next_version" == "v6.9.0" ]]; then
        print_success "✅ Minor bump test passed"
    else
        print_error "❌ Minor bump test failed - expected v6.9.0, got $next_version"
    fi
    
    echo
    
    # Test 3: Major bump (breaking changes)
    print_test "Test 3: Major bump with breaking changes"
    commits_breaking="feat!: change API contract
BREAKING CHANGE: schema migration
fix: update tests for new API"
    
    bump_type=$(determine_bump_type "$commits_breaking")
    next_version=$(calculate_next_version "v6.8.1" "$bump_type")
    
    print_info "Commits: $commits_breaking"
    print_info "Bump type: $bump_type"
    print_info "Next version: $next_version"
    
    if [[ "$next_version" == "v7.0.0" ]]; then
        print_success "✅ Major bump test passed"
    else
        print_error "❌ Major bump test failed - expected v7.0.0, got $next_version"
    fi
    
    echo
    
    # Test 4: No previous tag (first release)
    print_test "Test 4: First release (no previous tag)"
    commits_first="feat: initial release
feat: add core functionality
fix: resolve startup issues"
    
    bump_type=$(determine_bump_type "$commits_first")
    next_version=$(calculate_next_version "v0.0.0" "$bump_type")
    
    print_info "Commits: $commits_first"
    print_info "Bump type: $bump_type"
    print_info "Next version: $next_version"
    
    if [[ "$next_version" == "v0.1.0" ]]; then
        print_success "✅ First release test passed"
    else
        print_error "❌ First release test failed - expected v0.1.0, got $next_version"
    fi
    
    echo
    
    # Test 5: Mixed commits (should prioritize breaking changes)
    print_test "Test 5: Mixed commits with breaking change priority"
    commits_mixed="feat: add new feature
fix: resolve bug
chore: update documentation
BREAKING CHANGE: remove deprecated API
feat: another new feature"
    
    bump_type=$(determine_bump_type "$commits_mixed")
    next_version=$(calculate_next_version "v6.8.1" "$bump_type")
    
    print_info "Commits: $commits_mixed"
    print_info "Bump type: $bump_type"
    print_info "Next version: $next_version"
    
    if [[ "$bump_type" == "major" ]]; then
        print_success "✅ Mixed commits test passed (correctly prioritized breaking change)"
    else
        print_error "❌ Mixed commits test failed - expected major bump, got $bump_type"
    fi
    
    echo
}

# Test with real repository data
test_real_repository() {
    print_header "Testing with Real Repository Data"
    
    # Get current repository info
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_warning "Not in a git repository - skipping real repository test"
        return
    fi
    
    # Get last tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    print_info "Last tag: $last_tag"
    
    # Get recent commits
    if [[ "$last_tag" == "v0.0.0" ]]; then
        commits=$(git log --oneline -5 | cut -d' ' -f2-)
    else
        commits=$(git log "$last_tag..HEAD" --oneline | cut -d' ' -f2-)
    fi
    
    print_info "Recent commits:"
    echo "$commits" | sed 's/^/  /'
    echo
    
    # Determine next version
    bump_type=$(determine_bump_type "$commits")
    next_version=$(calculate_next_version "$last_tag" "$bump_type")
    
    print_info "Detected bump type: $bump_type"
    print_info "Proposed next version: $next_version"
    
    print_success "✅ Real repository analysis complete"
    echo
}

# Main execution
main() {
    print_header "Semantic Versioning Test Suite"
    echo
    
    # Run test cases
    test_semantic_versioning
    
    # Test with real repository
    test_real_repository
    
    print_header "Test Suite Complete! 🎉"
    print_success "All semantic versioning logic tests completed"
}

# Run tests
main "$@"
