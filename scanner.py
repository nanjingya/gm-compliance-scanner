#!/usr/bin/env python3
"""国密合规扫描器 - 检测代码中的非国标密码算法使用"""

import sys
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict

# ── 检测规则 ────────────────────────────────────────────────────────────────

NON_COMPLIANT = [
    # 非对称加密
    (r'\bRSA\b', 'RSA', '请替换为 SM2'),
    (r'\bDSA\b', 'DSA', '请替换为 SM2'),
    (r'\bECDSA\b', 'ECDSA', '请替换为 SM2'),
    (r'\bDH\b', 'DH', '请替换为 SM2 密钥交换'),
    # 对称加密
    (r'\bAES\b', 'AES', '请替换为 SM4'),
    (r'\bDES\b(?!K)', 'DES', '请替换为 SM4'),
    (r'\b3DES\b|\bTDES\b|\bTripleDES\b', '3DES', '请替换为 SM4'),
    (r'\bRC4\b|\bRC2\b', 'RC4/RC2', '已废弃，请替换为 SM4'),
    # 哈希
    (r'\bMD5\b', 'MD5', '请替换为 SM3'),
    (r'\bSHA[-_]?1\b', 'SHA1', '请替换为 SM3'),
    (r'\bSHA[-_]?256\b', 'SHA256', '建议替换为 SM3'),
    (r'\bSHA[-_]?512\b', 'SHA512', '建议替换为 SM3'),
    # 库/包
    (r'from\s+Crypto\b|import\s+Crypto\b', 'PyCrypto', '请改用 gmssl'),
    (r'from\s+cryptography\b|import\s+cryptography\b', 'cryptography', '注意确认是否使用了非国密算法'),
    (r'\bcrypto\.createCipher\b|\bcrypto\.createHash\b', 'Node crypto', '注意确认算法是否为国密'),
    (r'CryptoJS\.(AES|MD5|SHA)', 'CryptoJS非国密', '请替换为 SM 系列算法'),
]

COMPLIANT = [
    (r'\bSM2\b', 'SM2'),
    (r'\bSM3\b', 'SM3'),
    (r'\bSM4\b', 'SM4'),
    (r'\bSM9\b', 'SM9'),
    (r'from\s+gmssl\b|import\s+gmssl\b', 'gmssl'),
    (r'gm-crypto|tongsuojs|sm-crypto', '国密JS库'),
]

EXTENSIONS = {
    '.py', '.js', '.ts', '.vue', '.jsx', '.tsx',
    '.java', '.go', '.rs', '.c', '.cpp', '.h',
    '.cs', '.php', '.rb', '.swift', '.kt',
}

SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'dist', 'build', '.venv', 'venv'}

# ── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class Issue:
    file: str
    line: int
    algorithm: str
    suggestion: str
    code: str


@dataclass
class ScanResult:
    total_files: int = 0
    total_lines: int = 0
    issues: List[Issue] = field(default_factory=list)
    compliant_hits: List[Dict] = field(default_factory=list)

    @property
    def compliance_score(self):
        if not self.issues:
            return 100.0
        total = len(self.issues) + len(self.compliant_hits)
        return round(len(self.compliant_hits) / total * 100, 1) if total else 100.0


# ── 扫描核心 ─────────────────────────────────────────────────────────────────

def scan_file(path: Path, result: ScanResult):
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return

    lines = content.splitlines()
    result.total_files += 1
    result.total_lines += len(lines)

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(('#', '//', '/*', '*')):
            continue

        for pattern, algo, suggestion in NON_COMPLIANT:
            if re.search(pattern, line, re.IGNORECASE):
                result.issues.append(Issue(
                    file=str(path),
                    line=lineno,
                    algorithm=algo,
                    suggestion=suggestion,
                    code=stripped[:120]
                ))

        for pattern, algo in COMPLIANT:
            if re.search(pattern, line, re.IGNORECASE):
                result.compliant_hits.append({'file': str(path), 'line': lineno, 'algorithm': algo})


def scan_path(target: Path, result: ScanResult):
    if target.is_file():
        if target.suffix in EXTENSIONS:
            scan_file(target, result)
    elif target.is_dir():
        for p in target.rglob('*'):
            if any(d in p.parts for d in SKIP_DIRS):
                continue
            if p.is_file() and p.suffix in EXTENSIONS:
                scan_file(p, result)


# ── 输出格式 ─────────────────────────────────────────────────────────────────

def print_text(result: ScanResult, target: str):
    W = '\033[33m'
    R = '\033[31m'
    G = '\033[32m'
    B = '\033[34m'
    E = '\033[0m'

    print(f"\n{B}{'='*60}{E}")
    print(f"{B}  国密合规扫描报告{E}")
    print(f"{B}{'='*60}{E}")
    print(f"  扫描目标  : {target}")
    print(f"  扫描文件  : {result.total_files} 个")
    print(f"  扫描行数  : {result.total_lines} 行")
    score = result.compliance_score
    color = G if score >= 80 else (W if score >= 50 else R)
    print(f"  合规得分  : {color}{score}%{E}")
    print(f"  国密使用  : {G}{len(result.compliant_hits)} 处{E}")
    print(f"  违规发现  : {R if result.issues else G}{len(result.issues)} 处{E}")

    if result.issues:
        print(f"\n{R}── 违规详情 {'─'*44}{E}")
        by_file: Dict[str, List[Issue]] = {}
        for issue in result.issues:
            by_file.setdefault(issue.file, []).append(issue)

        for filepath, issues in by_file.items():
            print(f"\n  {W}{filepath}{E}")
            for i in issues:
                print(f"    {R}✗{E} 第{i.line:4d}行  [{W}{i.algorithm}{E}]  {i.suggestion}")
                print(f"         {i.code}")

    if result.compliant_hits:
        files = list({h['file'] for h in result.compliant_hits})
        print(f"\n{G}── 国密使用 {'─'*44}{E}")
        algos: Dict[str, int] = {}
        for h in result.compliant_hits:
            algos[h['algorithm']] = algos.get(h['algorithm'], 0) + 1
        for algo, count in sorted(algos.items(), key=lambda x: -x[1]):
            print(f"  {G}✓{E} {algo}: {count} 处")

    print(f"\n{B}{'='*60}{E}")
    if not result.issues:
        print(f"  {G}✓ 恭喜！未发现非国密算法使用{E}")
    else:
        print(f"  {R}! 发现 {len(result.issues)} 处需整改，建议优先处理高频文件{E}")
    print(f"{B}{'='*60}{E}\n")


def print_json(result: ScanResult, target: str):
    out = {
        "target": target,
        "summary": {
            "total_files": result.total_files,
            "total_lines": result.total_lines,
            "compliance_score": result.compliance_score,
            "issues_count": len(result.issues),
            "compliant_hits": len(result.compliant_hits),
        },
        "issues": [asdict(i) for i in result.issues],
        "compliant_hits": result.compliant_hits,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='国密合规扫描器 - 检测代码中的非国标密码算法',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python scanner.py scan ./my-project
  python scanner.py scan ./src --format json
  python scanner.py scan ./app.js --format json > report.json"""
    )
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_scan = sub.add_parser('scan', help='扫描目标路径')
    p_scan.add_argument('target', help='文件或目录路径')
    p_scan.add_argument('--format', choices=['text', 'json'], default='text', help='输出格式')

    args = parser.parse_args()

    if args.cmd == 'scan':
        target = Path(args.target)
        if not target.exists():
            print(f"错误: 路径不存在 - {target}", file=sys.stderr)
            sys.exit(1)

        result = ScanResult()
        scan_path(target, result)

        if args.format == 'json':
            print_json(result, str(target))
        else:
            print_text(result, str(target))

        sys.exit(1 if result.issues else 0)


if __name__ == '__main__':
    main()
