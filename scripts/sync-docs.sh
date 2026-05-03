#!/bin/bash
#
# sync-docs.sh - Sync documentation from docs/ to apps/website/public/docs/
#
# This script copies the documentation files from the main docs/ directory
# to the website's public directory so they can be served as static assets.
# It also generates a manifest file and adds a timestamp.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_SOURCE="$PROJECT_ROOT/docs"
DOCS_TARGET="$PROJECT_ROOT/apps/website/public/docs"
MANIFEST_FILE="$DOCS_TARGET/manifest.json"

echo "🔄 Syncing documentation..."
echo "   Source: $DOCS_SOURCE"
echo "   Target: $DOCS_TARGET"

# Create target directory if it doesn't exist
mkdir -p "$DOCS_TARGET"

# Remove old docs (except we might want to keep the directory)
rm -rf "$DOCS_TARGET"/*
mkdir -p "$DOCS_TARGET"

# Copy all markdown files while preserving structure
echo "📁 Copying documentation files..."
find "$DOCS_SOURCE" -type f -name "*.md" | while read -r file; do
    # Get relative path from docs source
    rel_path="${file#$DOCS_SOURCE/}"
    target_file="$DOCS_TARGET/$rel_path"
    
    # Create target directory
    target_dir=$(dirname "$target_file")
    mkdir -p "$target_dir"
    
    # Copy file
    cp "$file" "$target_file"
    echo "   ✓ $rel_path"
done

# Generate timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
HUMAN_READABLE=$(date -u +"%B %d, %Y at %H:%M UTC")

# Create manifest.json
echo "📝 Generating manifest..."
cat > "$MANIFEST_FILE" << EOF
{
  "generated_at": "$TIMESTAMP",
  "generated_at_human": "$HUMAN_READABLE",
  "source": "docs/",
  "files": [
EOF

# Add file list to manifest
first=true
find "$DOCS_TARGET" -type f -name "*.md" | sort | while read -r file; do
    rel_path="${file#$DOCS_TARGET/}"
    # Escape backslashes for JSON
    json_path=$(echo "$rel_path" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')
    
    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$MANIFEST_FILE.tmp"
    fi
    
    echo -n "    \"$json_path\"" >> "$MANIFEST_FILE.tmp"
done

# Close manifest JSON
if [ -f "$MANIFEST_FILE.tmp" ]; then
    cat "$MANIFEST_FILE.tmp" >> "$MANIFEST_FILE"
    rm "$MANIFEST_FILE.tmp"
fi

cat >> "$MANIFEST_FILE" << EOF

  ]
}
EOF

# Create timestamp file for the UI
cat > "$DOCS_TARGET/timestamp.json" << EOF
{
  "updated_at": "$TIMESTAMP",
  "updated_at_formatted": "$HUMAN_READABLE"
}
EOF

# Count files
FILE_COUNT=$(find "$DOCS_TARGET" -type f -name "*.md" | wc -l)

echo ""
echo "✅ Documentation sync complete!"
echo "   Files copied: $FILE_COUNT"
echo "   Generated at: $HUMAN_READABLE"
echo ""
echo "🚀 Next steps:"
echo "   cd apps/website && npm run dev"
