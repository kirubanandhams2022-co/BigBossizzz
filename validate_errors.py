#!/usr/bin/env python3
"""
BigBossizzz Error Prevention Validation
Checks for common issues that could cause recurring errors
"""

import sys
import os
import re
from pathlib import Path

def check_javascript_syntax_errors():
    """Check for question mark syntax errors in JS files"""
    js_files = Path('static/js').glob('*.js')
    issues = []
    
    for js_file in js_files:
        try:
            with open(js_file, 'r') as f:
                content = f.read()
            
            # Check for problematic console.log patterns
            if re.search(r'console\.log\s*\(\s*["'][\?]+', content):
                issues.append(f'{js_file}: Found question mark in console.log')
                
        except Exception as e:
            issues.append(f'{js_file}: Error reading file - {e}')
    
    return issues

def check_hardcoded_routes():
    """Check for hardcoded routes in JavaScript that should use url_for"""
    js_files = Path('static/js').glob('*.js')
    issues = []
    
    hardcoded_patterns = [
        r'href\s*:\s*["'][^{]*admin/',
        r'href\s*:\s*["'][^{]*host/',
        r'href\s*:\s*["'][^{]*participant/'
    ]
    
    for js_file in js_files:
        try:
            with open(js_file, 'r') as f:
                content = f.read()
            
            for pattern in hardcoded_patterns:
                if re.search(pattern, content):
                    issues.append(f'{js_file}: Found hardcoded route that could break')
                    
        except Exception as e:
            issues.append(f'{js_file}: Error reading file - {e}')
    
    return issues

def check_import_guards():
    """Check that optional imports have proper guards"""
    python_files = ['routes.py', 'app.py']
    issues = []
    
    dangerous_imports = [
        'pandas',
        'PyPDF2', 
        'docx',
        'lti_integration',
        'analytics_engine',
        'automated_proctoring_reports'
    ]
    
    for py_file in python_files:
        if not os.path.exists(py_file):
            continue
            
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            for import_name in dangerous_imports:
                # Check for unguarded imports
                if re.search(f'^import {import_name}', content, re.MULTILINE):
                    if not re.search(f'try:\s*
.*import {import_name}', content, re.DOTALL):
                        issues.append(f'{py_file}: Unguarded import of {import_name}')
                        
        except Exception as e:
            issues.append(f'{py_file}: Error reading file - {e}')
    
    return issues

def main():
    print('🔍 BigBossizzz Error Prevention Check')
    print('='*50)
    
    all_issues = []
    
    # Check JavaScript syntax errors
    js_issues = check_javascript_syntax_errors()
    if js_issues:
        print('
❌ JavaScript Syntax Issues:')
        for issue in js_issues:
            print(f'   {issue}')
        all_issues.extend(js_issues)
    else:
        print('
✅ No JavaScript syntax issues found')
    
    # Check hardcoded routes
    route_issues = check_hardcoded_routes()
    if route_issues:
        print('
❌ Hardcoded Route Issues:')
        for issue in route_issues:
            print(f'   {issue}')
        all_issues.extend(route_issues)
    else:
        print('
✅ No hardcoded route issues found')
    
    # Check import guards
    import_issues = check_import_guards()
    if import_issues:
        print('
❌ Import Guard Issues:')
        for issue in import_issues:
            print(f'   {issue}')
        all_issues.extend(import_issues)
    else:
        print('
✅ All imports properly guarded')
    
    print('
' + '='*50)
    if all_issues:
        print(f'❌ Found {len(all_issues)} issues that need fixing')
        return 1
    else:
        print('✅ All checks passed - no recurring error risks found!')
        return 0

if __name__ == '__main__':
    sys.exit(main())
