# GitHub Sync Safety Rules

## Pre-sync Validation

### 1. File Content Validation
- Always verify file content is not empty before creating issues
- Use reliable frontmatter extraction: `awk '/^---$/{if(++c==2) flag=1; next} flag' file.md`
- Avoid problematic sed patterns like `sed '1,/^---$/d; 1,/^---$/d'`

### 2. GitHub CLI Compatibility
- Test commands before batch operations
- Use fallback methods for older CLI versions
- Always capture and check command output

### 3. Duplicate Prevention
```bash
# Check for existing epics before creating
existing=$(gh issue list --label "epic" --search "Epic: $NAME" --json number -q '.[0].number // empty')
if [ -n "$existing" ]; then
  echo "⚠️ Epic #$existing already exists"
  # Handle appropriately
fi
```

## Safe Task Creation Pattern

```bash
create_task_issue() {
  local file="$1" title body issue_url issue_num

  # Validate file
  [ ! -f "$file" ] && return 1

  # Extract title safely
  title=$(awk '/^name:/ {sub(/^name: */, ""); print; exit}' "$file")
  [ -z "$title" ] && return 1

  # Extract body safely
  awk '/^---$/{if(++c==2) flag=1; next} flag' "$file" > /tmp/body.md
  [ ! -s /tmp/body.md ] && return 1

  # Create and verify
  issue_url=$(gh issue create --title "$title" --body-file /tmp/body.md)
  issue_num=$(echo "$issue_url" | grep -o '[0-9]*$')

  # Verify creation
  gh issue view "$issue_num" >/dev/null || return 1

  echo "$file:$issue_num"
}
```

## Recovery Procedures

### 1. Empty Issue Recovery
```bash
# Fix empty issues by re-uploading content
for issue in 6 7 8 9 10 11; do
  file=".claude/epics/$EPIC/${issue}.md"
  if [ -f "$file" ]; then
    awk '/^---$/{if(++c==2) flag=1; next} flag' "$file" > /tmp/fix-${issue}.md
    gh issue edit "$issue" --body-file "/tmp/fix-${issue}.md"
  fi
done
```

### 2. Duplicate Issue Cleanup
```bash
# Close duplicates with explanation
gh issue close $DUPLICATE_NUM --comment "Duplicate of #$MAIN_NUM. Using main issue for tracking."
```