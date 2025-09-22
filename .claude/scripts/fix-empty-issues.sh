#!/bin/bash
# Quick fix script for empty GitHub issues

fix_empty_issues() {
    local epic_name="$1"
    local epic_dir=".claude/epics/$epic_name"

    if [ ! -d "$epic_dir" ]; then
        echo "Epic directory not found: $epic_dir"
        return 1
    fi

    echo "Fixing empty issues for epic: $epic_name"

    local fixed=0
    local skipped=0

    # Process each task file that corresponds to a GitHub issue
    for task_file in "$epic_dir"/[0-9]*.md; do
        [ ! -f "$task_file" ] && continue

        local issue_num=$(basename "$task_file" .md)

        # Skip epic.md and non-numeric files
        if [[ ! "$issue_num" =~ ^[0-9]+$ ]]; then
            continue
        fi

        echo "Checking issue #$issue_num..."

        # Check if issue body is empty
        local current_body
        current_body=$(gh issue view "$issue_num" --json body -q '.body' 2>/dev/null)

        if [ -z "$current_body" ] || [ "$current_body" = "null" ]; then
            echo "  Issue #$issue_num is empty - fixing..."

            # Extract content using safe method
            if awk '/^---$/{if(++c==2) flag=1; next} flag' "$task_file" > "/tmp/fix-${issue_num}.md"; then
                if [ -s "/tmp/fix-${issue_num}.md" ]; then
                    # Update the issue
                    if gh issue edit "$issue_num" --body-file "/tmp/fix-${issue_num}.md"; then
                        echo "  ✅ Fixed issue #$issue_num"
                        ((fixed++))
                    else
                        echo "  ❌ Failed to update issue #$issue_num"
                    fi
                    rm -f "/tmp/fix-${issue_num}.md"
                else
                    echo "  ❌ No content extracted from $task_file"
                fi
            else
                echo "  ❌ Failed to extract content from $task_file"
            fi
        else
            echo "  ✅ Issue #$issue_num already has content"
            ((skipped++))
        fi
    done

    echo ""
    echo "Summary:"
    echo "  ✅ Fixed: $fixed issues"
    echo "  ⏭️ Skipped (already had content): $skipped issues"
}

# Usage example:
# fix_empty_issues "ai-system-prompt-generator"

if [ $# -eq 1 ]; then
    fix_empty_issues "$1"
else
    echo "Usage: $0 <epic-name>"
    echo "Example: $0 ai-system-prompt-generator"
fi