import os
import re

OUTPUT_ROOT = r"D:\Project\Papers\Ocr-markdown"
subjects = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]

def analyze_quality(filepath):
    """分析markdown文件的质量指标（不仅看数量，更看质量）"""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stats = {}
    
    # 1. 化学元素符号空格问题（如 S O_{2} 应为 SO_{2}）
    # 匹配模式：大写字母 + 空格 + 大写字母 + 下标
    chem_space_errors = re.findall(r'[A-Z]\s+[A-Z]\s*[_{]', content)
    # 更宽松的匹配：连续元素符号间有空格
    element_space_errors = re.findall(r'(?:Ca|Na|Fe|Cu|Zn|Al|Mg|K|Ba|Cl|SO|CO|NO|OH|NH)\s+(?:Cl|OH|O|H|N|S|C)', content)
    stats['chem_space_errors'] = len(chem_space_errors) + len(element_space_errors)
    
    # 2. 乱码字符检测
    garbled_chars = re.findall(r'[楓↑ε]', content)
    stats['garbled_chars'] = len(garbled_chars)
    
    # 3. 表格结构完整性（检测是否有明显的合并错乱）
    # 检测表格中是否有 rowspan/colspan 使用
    rowspan_usage = re.findall(r'rowspan', content)
    colspan_usage = re.findall(r'colspan', content)
    stats['complex_tables'] = len(rowspan_usage) + len(colspan_usage)
    
    # 4. LaTeX公式格式规范性
    # 检测 \mathrm{} 的使用（化学式常用）
    mathrm_usage = re.findall(r'\\mathrm\{[^}]*\}', content)
    stats['mathrm_formulas'] = len(mathrm_usage)
    
    # 5. 下标格式检测
    # 正确格式：_{...} 或 _x
    proper_subscripts = re.findall(r'_[{][^}]+[}]', content)
    # 可能错误的格式（空格在下标前）
    bad_subscripts = re.findall(r'\s+_\{', content)
    stats['proper_subscripts'] = len(proper_subscripts)
    stats['bad_subscripts'] = len(bad_subscripts)
    
    # 6. 上标格式检测
    proper_superscripts = re.findall(r'\^[{][^}]+[}]', content)
    stats['proper_superscripts'] = len(proper_superscripts)
    
    # 7. 图片引用完整性
    img_refs = re.findall(r'<img[^>]+src="([^"]+)"', content)
    stats['image_refs'] = len(img_refs)
    
    # 8. 文本连贯性（检测是否有断裂的句子）
    # 检测以标点符号开头的行（可能是断裂）
    broken_lines = re.findall(r'^[，。、；：！？）】]', content, re.MULTILINE)
    stats['broken_lines'] = len(broken_lines)
    
    # 9. 特殊符号识别
    # 检测常见的数学符号
    math_symbols = re.findall(r'[√∑∏∫≈≠≤≥±∞∈∉⊂⊃∪∩]', content)
    stats['math_symbols'] = len(math_symbols)
    
    # 10. 题号格式规范性
    # 规范格式：数字+点/顿号
    proper_questions = re.findall(r'^\d+[\.\．、]', content, re.MULTILINE)
    stats['proper_questions'] = len(proper_questions)
    
    return stats

def main():
    print("="*70)
    print("  PP-StructureV3 vs PaddleOCR-VL-1.6 全科质量对比分析")
    print("="*70)
    
    all_results = {}
    
    for subject in subjects:
        file3 = os.path.join(OUTPUT_ROOT, subject, "PP-StructureV3", f"{subject}.md")
        file16 = os.path.join(OUTPUT_ROOT, subject, "PaddleOCR-VL-1.6", f"{subject}.md")
        
        stats3 = analyze_quality(file3)
        stats16 = analyze_quality(file16)
        
        all_results[subject] = {'pp3': stats3, 'vl16': stats16}
    
    # 输出各科详细对比
    for subject in subjects:
        stats3 = all_results[subject]['pp3']
        stats16 = all_results[subject]['vl16']
        
        if not stats3 or not stats16:
            continue
        
        print(f"\n{'='*70}")
        print(f"  {subject}")
        print(f"{'='*70}")
        
        # 质量问题对比
        print(f"\n  [质量问题] (越少越好)")
        quality_metrics = [
            ('化学式空格错误', 'chem_space_errors'),
            ('乱码字符', 'garbled_chars'),
            ('断裂句子', 'broken_lines'),
            ('错误下标格式', 'bad_subscripts'),
        ]
        
        for label, key in quality_metrics:
            v3 = stats3.get(key, 0)
            v16 = stats16.get(key, 0)
            if v3 == 0 and v16 == 0:
                status = "  都无问题"
            elif v3 < v16:
                status = "  PP-V3更好"
            elif v16 < v3:
                status = "  VL-1.6更好"
            else:
                status = "  持平"
            print(f"    {label:<15} PP-V3: {v3:>5}  VL-1.6: {v16:>5}  {status}")
        
        # 结构完整性对比
        print(f"\n  [结构完整性]")
        structure_metrics = [
            ('复杂表格(合并单元格)', 'complex_tables'),
            ('LaTeX公式', 'mathrm_formulas'),
            ('规范下标', 'proper_subscripts'),
            ('规范上标', 'proper_superscripts'),
            ('图片引用', 'image_refs'),
            ('数学符号', 'math_symbols'),
            ('规范题号', 'proper_questions'),
        ]
        
        for label, key in structure_metrics:
            v3 = stats3.get(key, 0)
            v16 = stats16.get(key, 0)
            if v3 > v16:
                status = "  PP-V3更多"
            elif v16 > v3:
                status = "  VL-1.6更多"
            else:
                status = "  持平"
            print(f"    {label:<20} PP-V3: {v3:>5}  VL-1.6: {v16:>5}  {status}")
    
    # 汇总统计
    print(f"\n{'='*70}")
    print(f"  全科汇总统计")
    print(f"{'='*70}")
    
    # 统计各科胜出情况
    pp3_wins = 0
    vl16_wins = 0
    ties = 0
    
    quality_metrics = ['chem_space_errors', 'garbled_chars', 'broken_lines', 'bad_subscripts']
    
    print(f"\n  [质量问题统计] (错误总数)")
    print(f"  {'科目':<8} {'PP-StructureV3':>15} {'PaddleOCR-VL-1.6':>18} {'优势方':>10}")
    print(f"  {'-'*55}")
    
    total_pp3_errors = 0
    total_vl16_errors = 0
    
    for subject in subjects:
        stats3 = all_results[subject]['pp3']
        stats16 = all_results[subject]['vl16']
        
        if not stats3 or not stats16:
            continue
        
        pp3_errors = sum(stats3.get(m, 0) for m in quality_metrics)
        vl16_errors = sum(stats16.get(m, 0) for m in quality_metrics)
        
        total_pp3_errors += pp3_errors
        total_vl16_errors += vl16_errors
        
        if pp3_errors < vl16_errors:
            winner = "PP-V3"
            pp3_wins += 1
        elif vl16_errors < pp3_errors:
            winner = "VL-1.6"
            vl16_wins += 1
        else:
            winner = "平局"
            ties += 1
        
        print(f"  {subject:<8} {pp3_errors:>15} {vl16_errors:>18} {winner:>10}")
    
    print(f"  {'-'*55}")
    print(f"  {'合计':<8} {total_pp3_errors:>15} {total_vl16_errors:>18}")
    
    # 统计结构完整性
    print(f"\n  [结构完整性统计]")
    structure_metrics = ['proper_subscripts', 'proper_superscripts', 'image_refs', 'proper_questions']
    
    pp3_structure_wins = 0
    vl16_structure_wins = 0
    
    print(f"  {'科目':<8} {'PP-StructureV3':>15} {'PaddleOCR-VL-1.6':>18} {'优势方':>10}")
    print(f"  {'-'*55}")
    
    for subject in subjects:
        stats3 = all_results[subject]['pp3']
        stats16 = all_results[subject]['vl16']
        
        if not stats3 or not stats16:
            continue
        
        pp3_score = sum(stats3.get(m, 0) for m in structure_metrics)
        vl16_score = sum(stats16.get(m, 0) for m in structure_metrics)
        
        if pp3_score > vl16_score:
            winner = "PP-V3"
            pp3_structure_wins += 1
        elif vl16_score > pp3_score:
            winner = "VL-1.6"
            vl16_structure_wins += 1
        else:
            winner = "平局"
        
        print(f"  {subject:<8} {pp3_score:>15} {vl16_score:>18} {winner:>10}")
    
    # 最终结论
    print(f"\n{'='*70}")
    print(f"  最终结论")
    print(f"{'='*70}")
    print(f"\n  质量问题方面:")
    print(f"    PP-StructureV3 更优: {pp3_wins} 科")
    print(f"    PaddleOCR-VL-1.6 更优: {vl16_wins} 科")
    print(f"    持平: {ties} 科")
    print(f"\n  结构完整性方面:")
    print(f"    PP-StructureV3 更优: {pp3_structure_wins} 科")
    print(f"    PaddleOCR-VL-1.6 更优: {vl16_structure_wins} 科")
    
    print(f"\n  质量问题总数:")
    print(f"    PP-StructureV3: {total_pp3_errors} 个错误")
    print(f"    PaddleOCR-VL-1.6: {total_vl16_errors} 个错误")

if __name__ == "__main__":
    main()
