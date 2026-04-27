# 国密合规扫描器

> 检测代码中的非国标密码算法，助力国密改造合规审查

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![零依赖](https://img.shields.io/badge/依赖-零依赖-brightgreen.svg)]()

## 简介

`gm-compliance-scanner` 是一个轻量级的命令行工具，用于扫描代码仓库中使用的密码算法，识别不符合国密标准（GB/T）的算法调用，并给出替换建议。

适用于：
- **企业国密改造**：快速定位存量代码中的非国密算法
- **安全合规审查**：生成可交付的 JSON 格式扫描报告
- **CI/CD 集成**：扫描有违规时以非零退出码退出，可直接接入流水线

## 特性

- **零依赖**：仅使用 Python 标准库，无需安装任何第三方包
- **多语言支持**：Python、JavaScript/TypeScript、Java、Go、Rust、C/C++、PHP、Swift 等 15+ 种文件类型
- **双向检测**：同时检测违规算法和已有国密使用，输出合规得分
- **两种输出格式**：`text`（彩色终端报告）和 `json`（结构化数据，适合自动化处理）
- **智能跳过**：自动忽略 `node_modules`、`.git`、`dist` 等无关目录

## 检测范围

| 类型 | 违规算法 | 国密替代 |
|------|---------|---------|
| 非对称加密 | RSA、DSA、ECDSA、DH | SM2 |
| 对称加密 | AES、DES、3DES、RC4 | SM4 |
| 哈希算法 | MD5、SHA1、SHA256、SHA512 | SM3 |
| 密码库 | PyCrypto、cryptography、CryptoJS | gmssl、sm-crypto |

## 安装

```bash
git clone https://github.com/your-username/gm-compliance-scanner.git
cd gm-compliance-scanner
```

无需安装依赖，直接运行。

## 使用方法

### 扫描目录

```bash
python scanner.py scan ./your-project
```

### 扫描单个文件

```bash
python scanner.py scan ./src/crypto_utils.py
```

### 输出 JSON 报告

```bash
python scanner.py scan ./your-project --format json
python scanner.py scan ./your-project --format json > report.json
```

### 集成到 CI/CD

```bash
python scanner.py scan ./src
# 有违规时退出码为 1，无违规时为 0
echo $?
```

## 输出示例

**终端报告（text 格式）：**

```
============================================================
  国密合规扫描报告
============================================================
  扫描目标  : ./examples
  扫描文件  : 2 个
  扫描行数  : 34 行
  合规得分  : 33.3%
  国密使用  : 3 处
  违规发现  : 6 处

── 违规详情 ──────────────────────────────────────────────
  ./examples/test_non_compliant.py
    ✗ 第 2行  [PyCrypto]  请改用 gmssl
    ✗ 第 3行  [RSA]  请替换为 SM2
    ✗ 第 8行  [AES]  请替换为 SM4
    ✗ 第11行  [MD5]  请替换为 SM3

── 国密使用 ──────────────────────────────────────────────
  ✓ gmssl: 2 处
  ✓ SM4: 1 处
  ✓ SM3: 1 处
============================================================
  ! 发现 6 处需整改，建议优先处理高频文件
============================================================
```

**JSON 报告格式：**

```json
{
  "target": "./examples",
  "summary": {
    "total_files": 2,
    "total_lines": 34,
    "compliance_score": 33.3,
    "issues_count": 6,
    "compliant_hits": 3
  },
  "issues": [
    {
      "file": "./examples/test_non_compliant.py",
      "line": 3,
      "algorithm": "RSA",
      "suggestion": "请替换为 SM2",
      "code": "from Crypto.PublicKey import RSA"
    }
  ]
}
```

## 合规得分说明

```
得分 = 国密使用数 / (国密使用数 + 违规数) × 100%

≥ 80%  绿色 ✓  合规状态良好
≥ 50%  黄色 △  需要关注
< 50%  红色 ✗  需要重点整改
```

## 示例文件

`examples/` 目录包含两个演示文件：

- `test_non_compliant.py`：包含多种非国密算法调用（AES、RSA、MD5）
- `test_compliant.py`：全量使用国密算法（SM2、SM3、SM4）

```bash
# 运行示例
python scanner.py scan ./examples
```

## License

MIT
