# Enhanced Pattern Matching in Vertopal CLI

This document describes the enhanced pattern matching capabilities implemented in Vertopal CLI, providing powerful and flexible file selection options.

## Overview

The enhanced pattern matching system supports:

- **Brace Expansion**: `{a,b,c}` and `{1..5}` patterns
- **Bracket Expansion**: `[abc]` and `[0-9]` patterns (character classes and ranges)
- **Enhanced Wildcards**: Standard glob patterns with improvements
- **Recursive Patterns**: `**/*` for deep directory traversal
- **Advanced Exclusion**: Multiple pattern types for filtering
- **Date Filtering**: Filter files by modification date

## Basic Usage

```bash
# Convert a single file
vertopal convert document.pdf --to txt

# Convert multiple specific files
vertopal convert file1.pdf file2.docx file3.pptx --to txt

# Convert all PDFs in current directory
vertopal convert *.pdf --to txt

# Convert files in a directory recursively
vertopal convert ./documents/ --recursive --to txt
```

## Brace Expansion

Brace expansion allows you to specify multiple variations of a pattern in a concise way.

### List Expansion: `{a,b,c}`

```bash
# Convert specific months
vertopal convert report_{jan,feb,mar}.pdf --to txt

# Convert multiple document types
vertopal convert document_{draft,final,review}.docx --to txt

# Convert files with different extensions
vertopal convert data.{csv,json,xml} --to txt
```

### Range Expansion: `{1..5}`

```bash
# Convert numbered files
vertopal convert file_{1..10}.pdf --to txt

# Convert with zero-padding
vertopal convert chapter_{01..12}.docx --to txt

# Convert with step (using multiple patterns)
vertopal convert data_{1..10..2}.csv --to txt  # 1,3,5,7,9
```

### Nested Brace Expansion

```bash
# Complex patterns
vertopal convert report_{2023,2024}_{Q1,Q2,Q3,Q4}.pdf --to txt

# Multiple braces in single pattern
vertopal convert ./{a,b}/file-{1..5}.txt --to html

# Mixed range and list expansions
vertopal convert data_{1..3}_{csv,json,xml}.txt --to pdf

# Complex nested patterns
vertopal convert report_{2023,2024}_{Q1,Q2}_{draft,final}.pdf --to txt
```

### Enhanced Brace Expansion

The enhanced brace expansion system supports multiple braces in a single pattern, allowing for complex file selection:

```bash
# Multiple directory and file patterns
vertopal convert ./{docs,src,tests}/**/*.{txt,md,pdf} --to html

# Complex nested patterns with ranges
vertopal convert ./{a,b,c}/chapter_{01..12}_{draft,final}.docx --to pdf

# Mixed expansions for different file types
vertopal convert ./{2023,2024}/report_{Q1,Q2,Q3,Q4}_{jan,feb,mar}.{pdf,docx} --to txt

# Specific directory targeting with file ranges
vertopal convert ./{user1,user2,user3}/data_{1..100}_{csv,json}.txt --to pdf
```

This enhanced capability allows you to:

- Combine multiple directory selections with file patterns
- Use ranges and lists in the same pattern
- Create complex nested expansions
- Target specific file naming conventions across multiple directories

### Bracket Expansion

Bracket expansion allows you to specify character classes or ranges using square brackets, similar to shell globbing, but now with full support for multiple and nested bracket patterns:

```bash
# Single character class
vertopal convert file[123].txt --to pdf   # file1.txt, file2.txt, file3.txt

# Character range
vertopal convert file[a-c].txt --to pdf   # filea.txt, fileb.txt, filec.txt

# Multiple bracket expansions in one pattern
vertopal convert dir[1-2]/file[a-b].txt --to pdf   # dir1/filea.txt, dir1/fileb.txt, dir2/filea.txt, dir2/fileb.txt

# Combine with brace expansion
vertopal convert ./{a,b}/file[1-3].txt --to pdf   # ./a/file1.txt, ./a/file2.txt, ./a/file3.txt, ./b/file1.txt, ./b/file2.txt, ./b/file3.txt

# Complex nested patterns
vertopal convert ./data[1-2]_{A,B}/report[0-1].csv --to xlsx
```

Bracket expansion supports:

- Numeric ranges: `[0-9]`, `[1-5]`
- Alphabetic ranges: `[a-z]`, `[A-Z]`
- Character classes: `[abc]`, `[xyz]`
- Multiple bracket expansions in a single pattern
- Combination with brace expansion and wildcards

> **Note:** Bracket expansion is applied before glob wildcards. Patterns like `file[1-3]*.txt` will expand the brackets first, then apply the wildcard.

## Enhanced Wildcard Patterns

### Standard Wildcards

```bash
# Basic wildcards
vertopal convert *.pdf --to txt
vertopal convert document?.pdf --to txt
vertopal convert report_*.docx --to txt

# Character classes (bracket expansion)
vertopal convert file[0-9].pdf --to txt
vertopal convert report[a-z].docx --to txt
```

### Recursive Patterns

```bash
# Recursive directory search
vertopal convert **/*.pdf --to txt

# Recursive search in specific directory
vertopal convert ./docs/**/*.pdf --to txt

# Recursive search with specific depth (using exclude)
vertopal convert ./**/*.pdf --exclude "*/**/**" --to txt
```

## Advanced Exclusion Patterns

The `--exclude` option supports multiple pattern types for fine-grained filtering.

### Glob Patterns

```bash
# Exclude specific file types
vertopal convert **/*.pdf --exclude "*.tmp" "*.bak" --to txt

# Exclude files with specific names
vertopal convert **/*.docx --exclude "*draft*" "*temp*" --to txt

# Exclude specific directories
vertopal convert **/*.pdf --exclude "temp/*" "backup/*" --to txt
```

### Directory Patterns

```bash
# Exclude entire directories (end with /)
vertopal convert **/*.pdf --exclude "temp/" "backup/" --to txt

# Exclude nested directories
vertopal convert **/*.pdf --exclude "**/temp/" --to txt
```

### Regex Patterns

```bash
# Exclude using regex (start with ^)
vertopal convert **/*.pdf --exclude "^.*backup.*" --to txt

# Exclude files matching complex patterns
vertopal convert **/*.docx --exclude "^.*draft.*$" "^.*temp.*$" --to txt
```

## Date Filtering

Filter files based on modification date using the `--modified-since` option.

```bash
# Convert only recent files
vertopal convert **/*.pdf --modified-since 2024-01-01 --to txt

# Convert files modified this year
vertopal convert **/*.docx --modified-since 2024-01-01 --to txt

# Combine with other patterns
vertopal convert **/*.pdf --exclude "*draft*" --modified-since 2024-01-01 --to txt
```

## Real-World Examples

### Document Processing Workflows

```bash
# Convert all PDFs in a project, excluding drafts
vertopal convert ./project/**/*.pdf --exclude "*draft*" "*temp*" --to txt

# Convert only recent documents
vertopal convert ./documents/ --recursive --modified-since 2024-01-01 --to txt

# Convert specific document types, excluding backups
vertopal convert ./**/*.{pdf,docx,doc} --exclude "*backup*" "*draft*" --to txt

# Batch convert presentations
vertopal convert ./presentations/*.{ppt,pptx} --to pdf
```

### Content Management Scenarios

```bash
# Convert all documents in user folders
vertopal convert /home/*/Documents/**/*.{pdf,docx} --to txt

# Process only files with specific naming patterns
vertopal convert ./**/report_2024_*.{pdf,docx} --to txt

# Convert files by date ranges
vertopal convert ./**/*.pdf --modified-since 2024-01-01 --to txt
```

### Development & Automation

```bash
# Convert documentation files
vertopal convert ./docs/**/*.{md,rst} --to pdf

# Process configuration files
vertopal convert ./config/*.{json,yaml,yml} --to txt

# Convert backup files
vertopal convert ./backups/*.bak --to original_format
```

### Complex Pattern Examples

```bash
# Convert quarterly reports for multiple years
vertopal convert report_{2022,2023,2024}_{Q1,Q2,Q3,Q4}.pdf --to txt

# Convert numbered chapters with exclusions
vertopal convert chapter_{01..20}.docx --exclude "chapter_{05,10,15}.docx" --to txt

# Convert files by date and type
vertopal convert ./**/*.{pdf,docx} --exclude "*draft*" --modified-since 2024-01-01 --to txt

# Recursive conversion with multiple exclusions
vertopal convert ./**/*.pdf --exclude "temp/" "*backup*" "^.*draft.*$" --to txt
```

## Performance Considerations

- **Large Directories**: For directories with thousands of files, consider using more specific patterns
- **Recursive Searches**: Use `**/*` patterns carefully in large directory trees
- **Exclusion Patterns**: Order exclusions from most specific to least specific for better performance

## Error Handling

The system gracefully handles:

- Non-existent files or directories
- Invalid brace expansion patterns
- Malformed regex patterns in exclusions
- Invalid date formats

## Backward Compatibility

All existing patterns continue to work:

- Standard wildcards (`*`, `?`)
- Basic directory traversal
- Simple exclusion patterns
- File lists and stdin (`-`)

## Best Practices

1. **Use Specific Patterns**: Prefer specific patterns over broad ones for better performance
2. **Combine Filters**: Use multiple exclusion patterns for precise control
3. **Test Patterns**: Test complex patterns on a small subset first
4. **Document Patterns**: Keep complex patterns documented for team use
5. **Use Date Filters**: Leverage date filtering to process only relevant files

## Troubleshooting

### Common Issues

1. **Pattern Not Matching**: Check for typos and ensure proper escaping
2. **Too Many Files**: Use more specific patterns or add exclusions
3. **Performance Issues**: Avoid overly broad recursive patterns
4. **Unexpected Exclusions**: Review exclusion pattern order and specificity

### Debug Tips

- Start with simple patterns and build complexity gradually
- Test patterns on a small directory first
- Check file permissions and existence
<!-- - Use the `--silent` flag to reduce output during testing -->
