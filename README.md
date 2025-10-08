# PubMed Crawler & PDF Downloader

[English](#english) | [中文](#chinese)

> PDF download functionality from [arundasan91/pubmed_pdf_downloader](https://github.com/arundasan91/pubmed_pdf_downloader)

---

<a name="english"></a>
## English

### Quick Start

**Step 1: Search PubMed**

Create `search_config.json`:
```json
{
  "search_keywords": ["keyword1", "keyword2"],
  "email": "your@email.com",
  "mindate": "2024/01/01",
  "maxdate": "2025/07/16",
  "NCBI_api": "optional_api_key"
}
```

Run crawler:
```bash
python crawl.py
```

> **Note**: Script auto-detects API key. Without API: max 3 keywords. With API: max 10 keywords.

Output: `pubmed_ids.txt`

**Step 2: Extract Article Info**

```bash
python download.py
```

Outputs:
- `*.html` - Human-readable format
- `*.md` - AI-friendly format  
- `link_*.html/md` - Articles with GitHub links
- `pmcids.txt` - For PDF download
- `failed_ids.txt` - Failed extractions

**Step 3: Download PDFs**

```bash
cd pubmed_pdf_downloader-main
pip install .
python pubmed_pdf_downloader/downloader.py -pmf pmcids.txt -out fetched_pdfs -batch 5 -delay 10
```

PDFs saved to `fetched_pdfs/`, failed IDs in `unfetched_pmcids.tsv`

### Configuration Tips

- **Keywords**: See [PubMed search guide](https://pubmed.ncbi.nlm.nih.gov/help/#proximity-searching)
- **API Key**: Get from [NCBI account settings](http://www.ncbi.nlm.nih.gov/account/)
- **Link Filter**: Edit `download.py`, change `select_link=True` to `select_link=False` in the last line to disable GitHub link filtering

### Requirements

```bash
pip install requests pubmed-mapper markdown tqdm
```

---

<a name="chinese"></a>
## 中文

### 快速开始

**步骤1：搜索文献**

创建 `search_config.json`：
```json
{
  "search_keywords": ["关键词1", "关键词2"],
  "email": "你的邮箱@email.com",
  "mindate": "2024/01/01",
  "maxdate": "2025/07/16",
  "NCBI_api": "可选的API密钥"
}
```

运行爬虫：
```bash
python crawl.py
```

> **注意**：脚本会自动检测API密钥。无API：最多3个关键词。有API：最多10个关键词。

输出文件：`pubmed_ids.txt`

**步骤2：提取文章信息**

```bash
python download.py
```

生成文件：
- `*.html` - 人类可读格式
- `*.md` - AI友好格式
- `link_*.html/md` - 包含GitHub链接的文章
- `pmcids.txt` - 用于下载PDF
- `failed_ids.txt` - 提取失败的ID

**步骤3：下载PDF**

```bash
cd pubmed_pdf_downloader-main
pip install .
python pubmed_pdf_downloader/downloader.py -pmf pmcids.txt -out fetched_pdfs -batch 5 -delay 10
```

PDF保存至 `fetched_pdfs/`，失败的ID记录在 `unfetched_pmcids.tsv`

### 配置说明

- **关键词格式**：参考 [PubMed搜索指南](https://pubmed.ncbi.nlm.nih.gov/help/#proximity-searching)
- **API申请**：访问 [NCBI账户设置](http://www.ncbi.nlm.nih.gov/account/)
- **链接筛选**：编辑 `download.py`，将最后一行的 `select_link=True` 改为 `select_link=False` 可关闭GitHub链接筛选

### 环境要求

```bash
pip install requests pubmed-mapper markdown tqdm
```
