"""从预审报告挑试点文件：9 科全覆盖，核心 6 科优先，覆盖典型问题形态。"""
import json
from pathlib import Path
from collections import defaultdict

r = json.load(open(r'D:\Project\Papers\reports\prereview_report_full.json', encoding='utf-8'))
by_file = {x['file']: x for x in r}

# 样本 94 份清单
sample = json.load(open(r'D:\Project\Papers\Ocr-markdown\auto-annotated-v6\review_sample.json', encoding='utf-8'))
sample_files = [s['file'] for s in sample['sample']]

CORE = ['语文', '数学', '英语', '物理', '化学', '生物']
REST = ['政治', '历史', '地理']


def subject_of(f):
    parts = Path(f).parts
    i = parts.index('auto-annotated-v6')
    return parts[i + 2]


picks = []
used_subjects = defaultdict(int)
want_codes = ['ANSWER_IN_TABLE', 'ANSWER_IN_RANGE', 'Q_BLOCK_MERGED_INDEPENDENT',
              'ANSWER_ZONE_UNANNOTATED', 'MATERIAL_OUTSIDE', 'BOILERPLATE_INCLUDED']

# 轮次1：核心科各挑1份"不合格"或"需返修"（优先覆盖不同问题码）
for subj in CORE:
    cands = [f for f in sample_files if subject_of(f) == subj and by_file[f]['verdict'] in ('不合格', '需返修')]
    # 优先挑问题码覆盖多的
    def score(f):
        codes = set(i['code'] for i in by_file[f]['issues'])
        return len(codes & set(want_codes)) * 10 + len(by_file[f]['issues'])
    cands.sort(key=score, reverse=True)
    if cands:
        picks.append(cands[0])
        used_subjects[subj] += 1

# 轮次2：其余3科各挑1份
for subj in REST:
    cands = [f for f in sample_files if subject_of(f) == subj and by_file[f]['verdict'] in ('不合格', '需返修', '基本合格(有提示)')]
    def score(f):
        codes = set(i['code'] for i in by_file[f]['issues'])
        return len(codes & set(want_codes)) * 10 + len(by_file[f]['issues'])
    cands.sort(key=score, reverse=True)
    if cands:
        picks.append(cands[0])

# 轮次3：核心科补2份（覆盖剩余典型形态：答案表格/区间连写优先）
for subj in CORE:
    if used_subjects[subj] >= 2:
        continue
    cands = [f for f in sample_files if subject_of(f) == subj and f not in picks
             and any(i['code'] in ('ANSWER_IN_TABLE', 'ANSWER_IN_RANGE') for i in by_file[f]['issues'])]
    if not cands:
        cands = [f for f in sample_files if subject_of(f) == subj and f not in picks]
    if cands:
        picks.append(cands[0])
        used_subjects[subj] += 1

# 轮次4：补1份"合格"作对照
clean = [f for f in sample_files if by_file[f]['verdict'] == '合格']
if clean:
    picks.append(clean[0])

out = []
for f in picks:
    x = by_file[f]
    out.append({
        'file': f,
        'subject': subject_of(f),
        'verdict': x['verdict'],
        'codes': [i['code'] for i in x['issues']],
        'questions': x['info'].get('questions'),
        'answers': x['info'].get('answers'),
    })

print(json.dumps(out, ensure_ascii=False, indent=1))
Path(r'D:\Project\Papers\data\reslice_pilot_files.json').write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(f"\n共 {len(out)} 份试点")
