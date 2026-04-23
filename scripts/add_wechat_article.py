#!/usr/bin/env python3
"""
手动添加公众号解读文章到数据库
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
ARTICLES_FILE = ROOT / "data" / "wechat_articles.json"


def add_article(url, title, source_account, category, notes=""):
    """添加公众号文章到数据库"""
    
    # 加载现有数据
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"articles": []}
    
    # 添加新文章
    article = {
        "title": title,
        "url": url,
        "source": source_account,
        "category": category,  # eu_mdr, fda, nmpa, imdrf, general
        "date": datetime.now().strftime("%Y-%m-%d"),
        "notes": notes,
        "added_at": datetime.now().isoformat()
    }
    
    data["articles"].append(article)
    
    # 保存
    ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Article added: {title}")
    print(f"Total articles: {len(data['articles'])}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python add_wechat_article.py <url> <title> <source_account> <category> [notes]")
        sys.exit(1)
    
    add_article(
        sys.argv[1],      # url
        sys.argv[2],      # title
        sys.argv[3],      # source_account
        sys.argv[4],      # category
        sys.argv[5] if len(sys.argv) > 5 else ""  # notes (optional)
    )
