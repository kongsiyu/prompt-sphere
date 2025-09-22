#!/bin/bash
# Safe Task Creation Template - Use this for GitHub sync operations

# Function: Safe content extraction from task files
extract_task_content() {
    local task_file="$1"
    local output_file="$2"

    # Validate input file exists
    if [ ! -f "$task_file" ]; then
        echo "ERROR: Task file not found: $task_file" >&2
        return 1
    fi

    # Extract content using safe AWK method
    if ! awk '/^---$/{if(++c==2) flag=1; next} flag' "$task_file" > "$output_file"; then
        echo "ERROR: Failed to extract content from $task_file" >&2
        return 1
    fi

    # Validate extracted content is not empty
    if [ ! -s "$output_file" ]; then
        echo "ERROR: Extracted content is empty for $task_file" >&2
        echo "Frontmatter format may be incorrect" >&2
        return 1
    fi

    return 0
}

# Function: Safe task name extraction
extract_task_name() {
    local task_file="$1"

    # Multiple extraction methods for robustness
    local task_name
    task_name=$(awk '/^name:/ {sub(/^name: */, ""); print; exit}' "$task_file")

    if [ -z "$task_name" ]; then
        # Fallback: try to get from first heading
        task_name=$(awk '/^---$/{if(++c==2) flag=1; next} flag && /^# / {sub(/^# */, ""); print; exit}' "$task_file")
    fi

    if [ -z "$task_name" ]; then
        echo "ERROR: Could not extract task name from $task_file" >&2
        return 1
    fi

    echo "$task_name"
}

# Function: Safe GitHub issue creation
create_github_issue_safe() {
    local task_file="$1"
    local task_name task_body issue_url issue_num

    echo "Processing: $task_file"

    # Step 1: Extract task name
    if ! task_name=$(extract_task_name "$task_file"); then
        return 1
    fi
    echo "  Task name: $task_name"

    # Step 2: Extract content
    local temp_body="/tmp/task-body-$(basename "$task_file").md"
    if ! extract_task_content "$task_file" "$temp_body"; then
        return 1
    fi
    echo "  Content extracted: $(wc -l < "$temp_body") lines"

    # Step 3: Check GitHub CLI compatibility
    local use_json=false
    if gh issue create --help 2>/dev/null | grep -q '\-\-json'; then
        use_json=true
    fi

    # Step 4: Create GitHub issue
    echo "  Creating GitHub issue..."
    if [ "$use_json" = true ]; then
        # Try with JSON output
        if issue_url=$(gh issue create --title "$task_name" --body-file "$temp_body" --json url -q .url 2>/dev/null); then
            issue_num=$(echo "$issue_url" | grep -o '[0-9]*$')
        else
            # Fallback to standard method
            issue_url=$(gh issue create --title "$task_name" --body-file "$temp_body")
            issue_num=$(echo "$issue_url" | grep -o '[0-9]*$')
        fi
    else
        # Standard method
        issue_url=$(gh issue create --title "$task_name" --body-file "$temp_body")
        issue_num=$(echo "$issue_url" | grep -o '[0-9]*$')
    fi

    # Step 5: Verify creation
    if [ -z "$issue_num" ]; then
        echo "  ERROR: Could not extract issue number from: $issue_url" >&2
        return 1
    fi

    # Verify issue exists
    if ! gh issue view "$issue_num" >/dev/null 2>&1; then
        echo "  ERROR: Issue verification failed for #$issue_num" >&2
        return 1
    fi

    echo "  ✅ Created: $issue_url (#$issue_num)"
    echo "$task_file:$issue_num"

    # Cleanup
    rm -f "$temp_body"
    return 0
}

# Function: Batch task creation with verification
create_tasks_batch_safe() {
    local epic_dir="$1"
    local mapping_file="${2:-/tmp/task-mapping.txt}"

    echo "Creating GitHub issues for tasks in: $epic_dir"

    # Initialize mapping file
    > "$mapping_file"

    local created=0
    local failed=0

    # Process each task file
    for task_file in "$epic_dir"/[0-9][0-9][0-9].md; do
        [ ! -f "$task_file" ] && continue

        if create_github_issue_safe "$task_file" >> "$mapping_file"; then
            ((created++))
            echo "Progress: $created created"

            # Brief pause to avoid API rate limits
            sleep 1
        else
            ((failed++))
            echo "⚠️ Failed to create issue for: $task_file"
        fi
    done

    echo ""
    echo "Summary:"
    echo "  ✅ Successfully created: $created issues"
    echo "  ❌ Failed: $failed issues"
    echo "  📄 Mapping saved to: $mapping_file"

    if [ $failed -gt 0 ]; then
        echo "⚠️ Some issues failed. Check above for details."
        return 1
    fi

    return 0
}

# Example usage:
# create_tasks_batch_safe ".claude/epics/my-epic" "/tmp/my-mapping.txt"