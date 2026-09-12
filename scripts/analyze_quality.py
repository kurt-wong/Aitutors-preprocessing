import os
import re

OUTPUT_ROOT = r"D:\Project\Papers\Ocr-markdown"
subjects = ["数学", "物理", "化学"]

def analyze_markdown(filepath):
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    stats = {
        'total_chars': len(content),
        'total_lines': len(lines),
        'non_empty_lines': sum(1 for l in lines if l.strip()),
    }
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_words = len(re.findall(r'[a-zA-Z]+', content))
    stats['chinese_chars'] = chinese_chars
    stats['english_words'] = english_words
    
    inline_formulas = re.findall(r'\$[^$]+\$', content)
    display_formulas = re.findall(r'\$\$[^$]+\$\$', content)
    stats['inline_formulas'] = len(inline_formulas)
    stats['display_formulas'] = len(display_formulas)
    
    subscripts = re.findall(r'_[{]?[^} \n]+[}]?', content)
    superscripts = re.findall(r'\^[{]?[^} \n]+[}]?', content)
    stats['subscripts'] = len(subscripts)
    stats['superscripts'] = len(superscripts)
    
    chem_formulas = re.findall(r'\\mathrm\{[^}]+\}', content)
    stats['chem_formulas'] = len(chem_formulas)
    
    html_tables = re.findall(r'<table[^>]*>.*?</table>', content, re.DOTALL)
    stats['tables'] = len(html_tables)
    table_rows = re.findall(r'<tr>', content)
    table_cells = re.findall(r'<td[^>]*>', content)
    stats['table_rows'] = len(table_rows)
    stats['table_cells'] = len(table_cells)
    
    images = re.findall(r'<img[^>]+>', content)
    stats['images'] = len(images)
    
    h1 = re.findall(r'^# .+', content, re.MULTILINE)
    h2 = re.findall(r'^## .+', content, re.MULTILINE)
    h3 = re.findall(r'^### .+', content, re.MULTILINE)
    stats['h1'] = len(h1)
    stats['h2'] = len(h2)
    stats['h3'] = len(h3)
    
    questions = re.findall(r'^\d+[\.\．、]', content, re.MULTILINE)
    stats['questions'] = len(questions)
    
    answers = re.findall(r'【答案】', content)
    analyses = re.findall(r'【解析】', content)
    stats['answers'] = len(answers)
    stats['analyses'] = len(analyses)
    
    space_issues = re.findall(r'[A-Z]\s+[A-Z][_{]', content)
    stats['space_issues'] = len(space_issues)
    
    garbled = re.findall(r'[楓↑ε]', content)
    stats['garbled_chars'] = len(garbled)
    
    return stats

def main():
    print("="*60)
    print("  PP-StructureV3 vs PaddleOCR-VL-1.6 全面对比分析")
    print("="*60)
    
    all_stats3 = {}
    all_stats16 = {}
    
    for subject in subjects:
        file3 = os.path.join(OUTPUT_ROOT, subject, "PP-StructureV3", f"{subject}.md")
        file16 = os.path.join(OUTPUT_ROOT, subject, "PaddleOCR-VL-1.6", f"{subject}.md")
        
        stats3 = analyze_markdown(file3)
        stats16 = analyze_markdown(file16)
        all_stats3[subject] = stats3
        all_stats16[subject] = stats16
        
        print(f"\n{'='*60}")
        print(f"  {subject} 科目对比")
        print(f"{'='*60}")
        
        metrics = [
            ('基础', [('总字符', 'total_chars'), ('非空行', 'non_empty_lines')]),
            ('文本', [('中文字符', 'chinese_chars'), ('英文单词', 'english_words')]),
            ('公式', [('行内公式', 'inline_formulas'), ('行间公式', 'display_formulas')]),
            ('上下标', [('下标', 'subscripts'), ('上标', 'superscripts')]),
            ('化学', [('化学式', 'chem_formulas')]),
            ('表格', [('表格数', 'tables'), ('单元格', 'table_cells')]),
            ('配图', [('图片数', 'images')]),
            ('题目', [('题目数', 'questions'), ('答案', 'answers'), ('解析', 'analyses')]),
            ('质量', [('空格问题', 'space_issues'), ('乱码', 'garbled_chars')]),
        ]
        
        for category, items in metrics:
            print(f"\n  [{category}]")
            for label, key in items:
                v3 = stats3.get(key, 0) if stats3 else 0
                v16 = stats16.get(key, 0) if stats16 else 0
                diff = v16 - v3
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                print(f"    {label:<10} PP-V3: {v3:>8}  VL-1.6: {v16:>8}  差异: {diff_str:>8}")
    
    # 汇总
    print(f"\n{'='*60}")
    print(f"  三科汇总")
    print(f"{'='*60}")
    
    summary_metrics = [
        ('中文字符', 'chinese_chars', False),
        ('行内公式', 'inline_formulas', False),
        ('下标', 'subscripts', False),
        ('上标', 'superscripts', False),
        ('表格单元格', 'table_cells', False),
        ('配图', 'images', False),
        ('题目数', 'questions', False),
        ('空格问题', 'space_issues', True),  # 越少越好
        ('乱码字符', 'garbled_chars', True),   # 越少越好
    ]
    
    print(f"\n  {'指标':<12} {'PP-StructureV3':>15} {'PaddleOCR-VL-1.6':>18} {'优势方':>10}")
    print(f"  {'-'*55}")
    
    for label, metric, lower_better in summary_metrics:
        total3 = sum(all_stats3[s].get(metric, 0) for s in subjects if all_stats3[s])
        total16 = sum(all_stats16[s].get(metric, 0) for s in subjects if all_stats16[s])
        
        if lower_better:
            winner = "VL-1.6" if total16 < total3 else ("PP-V3" if total3 < total16 else "平局")
        else:
            winner = "VL-1.6" if total16 > total3 else ("PP-V3" if total3 > total16 else "平局")
        
        print(f"  {label:<12} {total3:>15} {total16:>18} {winner:>10}")

if __name__ == "__main__":
    main()
