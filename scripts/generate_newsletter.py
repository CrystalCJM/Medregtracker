#!/usr/bin/env python3
"""
根据查新报告和公众号文章生成 Newsletter Markdown
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_wechat_articles():
    """加载公众号文章数据库"""
    articles_file = ROOT / "data" / "wechat_articles.json"
    if not articles_file.exists():
        return []
    
    with open(articles_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 只返回最近两周的文章
    cutoff = datetime.now() - timedelta(days=14)
    recent = []
    for article in data.get("articles", []):
        try:
            article_date = datetime.strptime(article["date"], "%Y-%m-%d")
            if article_date >= cutoff:
                recent.append(article)
        except:
            continue
    
    return recent


def generate_newsletter(report_file):
    with open(report_file, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    updates = report.get("updates", [])
    date_str = report.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    # 加载公众号文章
    wechat_articles = load_wechat_articles()
    
    # 按类别分组公众号文章
    articles_by_category = {
        "eu_mdr": [],
        "fda": [],
        "nmpa": [],
        "imdrf": [],
        "general": []
    }
    for article in wechat_articles:
        cat = article.get("category", "general")
        articles_by_category.setdefault(cat, []).append(article)
    
    lines = [
        f"# 法规更新周报 ({date_str})",
        "",
        f"> 覆盖周期：{date_str}",
        "> 本报告由自动化系统生成，仅供内部参考",
        "",
        "---",
        "",
    ]
    
    # ========== 第一部分：法规原文更新 ==========
    lines.append("## 一、法规原文更新")
    lines.append("")
    
    if not updates:
        lines.append("本周暂无重要法规更新。")
        lines.append("")
    else:
        for u in updates:
            lines.append(f"### {u['source']}")
            lines.append("")
            lines.append("| 序号 | 更新主题 | 日期 | 原文链接 |")
            lines.append("|------|---------|------|---------|")
            
        lines.append("| 序号 | 解读主题 | 来源公众号 | 日期 | 链接 | 备注 |")
        lines.append("|------|---------|-----------|------|------|------|")
        
        for i, article in enumerate(wechat_articles, 1):
            title = article.get("title", "")
            source = article.get("source", "")
            date = article.get("date", "")
            url = article.get("url", "")
            notes = article.get("notes", "")
            
            lines.append(f"| {i} | {title} | {source} | {date} | [链接]({url}) | {notes} |")
        lines.append("")
    
    # ========== 第二部分：行业解读与参考资料 ==========
    lines.append("---")
    lines.append("")
    lines.append("## 二、行业解读与参考资料")
    lines.append("")
    
    # 公众号文章表格
    if wechat_articles:
        lines.append("| 序号 | 解读主题 | 来源公众号 | 日期 | 链接 | 备注 |")
        lines.append("|------|---------|-----------|------|------|------|")
        
        for i, article in enumerate(wechat_articles, 1):
            title = article.get("title", "")
            source = article.get("source", "")
            date = article.get("date", "")
            url = article.get("url", "")
            notes = article.get("notes", "")
            
            lines.append(f"| {i} | {title} | {source} | {date} | [链接]({url}) | {notes} |")
        lines.append("")
    else:
        lines.append("本周暂无收集到公众号解读文章。")
        lines.append("")
    
    # ========== 第三部分：重点关注提醒 ==========
    lines.append("---")
    lines.append("")
    lines.append("## 三、重点关注提醒")
    lines.append("")
    lines.append("- [ ] EU MDR 最新协调标准更新")
    lines.append("- [ ] FDA 新发布指导原则")
    lines.append("- [ ] NMPA/CMDE 新法规/指导原则")
    lines.append("- [ ] Team-NB 立场文件")
    lines.append("- [ ] IMDRF 技术文件")
    lines.append("")
    
    # 页脚
    lines.extend([
        "---",
        "",
        "*如有疑问，请联系法规事务部*",
        "",
        f"*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ])
    
    content = "\n".join(lines)
    
    # 保存
    output_dir = ROOT / "docs" / "newsletters"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{date_str}-newsletter.md"
    output.write_text(content, encoding="utf-8")
    
    print(f"\nNewsletter 已生成: {output}")
    return output


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_newsletter.py <report.json>")
        sys.exit(1)
    
    generate_newsletter(sys.argv[1])
