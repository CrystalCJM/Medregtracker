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
        "> 本报告由自动化系统生成，仅供内部参考",
        "",
        "---",
        "",
        "## 本周概览",
        "",
    ]
    
    if not updates:
        lines.append("本周暂无重要法规更新。")
    else:
        lines.append(f"本周共发现 **{len(updates)}** 个来源有更新：")
        lines.append("")
        for u in updates:
            lines.append(f"- **{u['source']}**：{u['count']} 条")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("## 详细更新")
        lines.append("")
        
        for u in updates:
            lines.append(f"### {u['source']}")
            lines.append("")
            for item in u.get("new_items", []):
                title = item.get("title", "")
                link = item.get("link", "")
                
                if link and link != "Unknown":
                    lines.append(f"- [{title}]({link})")
                else:
                    lines.append(f"- {title}")
            lines.append("")
    
    lines.extend([
        "---",
        "",
        "## 重点关注提醒",
        "",
        "- [ ] EU MDR 最新协调标准更新",
        "- [ ] FDA 新发布指导原则",
        "- [ ] NMPA/CMDE 新法规/指导原则",
        "- [ ] Team-NB 立场文件",
        "- [ ] IMDRF 技术文件",
        "",
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
