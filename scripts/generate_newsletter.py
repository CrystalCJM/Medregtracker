#!/usr/bin/env python3
"""
根据查新报告生成 Newsletter Markdown
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent


def generate_newsletter(report_file):
    with open(report_file, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    updates = report.get("updates", [])
    date_str = report.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    lines = [
        f"# 法规更新周报 ({date_str})",
        "",
        f"> 覆盖周期：{date_str}",
        "> 本报告由自动化系统生成，仅供内部参考",
        "",
        "---",
        "",
        "## 一、法规原文更新",
        "",
    ]
    
    if not updates:
        lines.append("本周暂无重要法规更新。")
        lines.append("")
    else:
        for u in updates:
            lines.append(f"### {u['source']}")
            lines.append("")
            lines.append("| 序号 | 更新主题 | 日期 | 原文链接 |")
            lines.append("|------|---------|------|---------|")
            
            for i, item in enumerate(u.get("new_items", []), 1):
                title = item.get("title", "")
                link = item.get("link", "")
                date = item.get("date", "")
                
                if link and link != "Unknown":
                    lines.append(f"| {i} | {title} | {date} | [链接]({link}) |")
                else:
                    lines.append(f"| {i} | {title} | {date} | - |")
            lines.append("")
    
    lines.extend([
        "---",
        "",
        "## 二、重点关注提醒",
        "",
        "- [ ] EU MDR 最新协调标准更新",
        "- [ ] FDA 新发布指导原则",
        "- [ ] NMPA/CMDE 新法规/指导原则",
        "- [ ] Team-NB 立场文件",
        "- [ ] IMDRF 技术文件",
        "",
        "---",
        "",
        "*如有疑问，请联系JM*",
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
