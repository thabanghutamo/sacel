#!/usr/bin/env python3
"""
Template validation script to check for common issues
"""

import os
import re
from pathlib import Path

def check_template_issues():
    """Check for common template issues"""
    template_dir = Path("app/templates")
    
    print("🔍 TEMPLATE VALIDATION")
    print("=" * 40)
    
    issues = []
    files_checked = 0
    
    # Walk through all template files
    for template_file in template_dir.rglob("*.html"):
        files_checked += 1
        relative_path = template_file.relative_to(template_dir)
        
        try:
            content = template_file.read_text(encoding='utf-8')
            
            print(f"\n📄 Checking: {relative_path}")
            
            file_issues = []
            
            # Check for basic template structure
            if not content.strip():
                file_issues.append("Empty file")
            
            # Check for extends statements
            extends_matches = re.findall(r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}', content)
            if extends_matches:
                print(f"  📂 Extends: {extends_matches[0]}")
                
                # Check if extended template exists
                extended_template = Path(template_dir) / extends_matches[0]
                if not extended_template.exists():
                    file_issues.append(f"Extended template not found: {extends_matches[0]}")
            
            # Check for block definitions
            block_defs = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
            if block_defs:
                print(f"  📋 Blocks defined: {', '.join(block_defs)}")
            
            # Check for endblock statements
            endblock_count = len(re.findall(r'{%\s*endblock\s*%}', content))
            if len(block_defs) != endblock_count:
                file_issues.append(f"Mismatched blocks: {len(block_defs)} block starts, {endblock_count} endblocks")
            
            # Check for orphaned endblocks
            orphaned_endblocks = re.findall(r'{%\s*endblock\s*%}(?!\s*{%\s*block)', content)
            if orphaned_endblocks and not block_defs:
                file_issues.append("Orphaned endblock without matching block")
            
            # Check for syntax issues
            if '{%' in content and '%}' not in content:
                file_issues.append("Unmatched template tags")
            
            # Check for url_for patterns
            url_for_matches = re.findall(r"url_for\(['\"]([^'\"]+)['\"]", content)
            if url_for_matches:
                print(f"  🔗 URL references: {len(url_for_matches)} found")
                # Check for potential issues
                for url_ref in url_for_matches:
                    if '.' not in url_ref:
                        file_issues.append(f"Invalid URL reference (missing blueprint): {url_ref}")
            
            # Report issues for this file
            if file_issues:
                print(f"  ❌ Issues found: {len(file_issues)}")
                for issue in file_issues:
                    print(f"    • {issue}")
                issues.extend([(str(relative_path), issue) for issue in file_issues])
            else:
                print(f"  ✅ No issues found")
                
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            print(f"  💥 {error_msg}")
            issues.append((str(relative_path), error_msg))
    
    # Summary
    print(f"\n{'='*40}")
    print(f"📊 SUMMARY")
    print(f"Files checked: {files_checked}")
    print(f"Issues found: {len(issues)}")
    
    if issues:
        print(f"\n❌ ISSUES TO FIX:")
        for file_path, issue in issues:
            print(f"  {file_path}: {issue}")
    else:
        print(f"\n✅ All templates are valid!")
    
    return issues

def check_critical_templates():
    """Check if critical templates exist and are not empty"""
    print(f"\n🎯 CRITICAL TEMPLATE CHECK")
    print("-" * 30)
    
    critical_templates = [
        "base/layout.html",
        "base/dashboard_layout.html", 
        "students/dashboard.html",
        "teachers/dashboard.html",
        "admin/dashboard.html",
        "auth/login.html",
        "public/home.html"
    ]
    
    missing = []
    empty = []
    
    for template in critical_templates:
        template_path = Path(f"app/templates/{template}")
        
        if not template_path.exists():
            missing.append(template)
            print(f"  ❌ Missing: {template}")
        else:
            content = template_path.read_text(encoding='utf-8')
            if not content.strip():
                empty.append(template)
                print(f"  ⚠️  Empty: {template}")
            else:
                print(f"  ✅ OK: {template}")
    
    return missing, empty

if __name__ == '__main__':
    print("🚀 Starting template validation...")
    
    # Check for template issues
    issues = check_template_issues()
    
    # Check critical templates
    missing, empty = check_critical_templates()
    
    print(f"\n{'='*40}")
    print("🎯 RECOMMENDATIONS")
    
    if issues:
        print("1. 🔧 Fix template syntax issues listed above")
    
    if missing:
        print("2. 📄 Create missing critical templates")
    
    if empty:
        print("3. ✏️  Add content to empty templates")
    
    if not issues and not missing and not empty:
        print("✅ All templates are in good shape!")
        print("🔍 Issue might be in authentication/routing logic")
    
    print(f"\n✅ Validation complete!")