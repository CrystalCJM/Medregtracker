#!/usr/bin/env python3
"""
法规查新脚本 - 检查6个来源的更新
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.parent
STATE_FILE = ROOT / "data" / "update_state.json"

SOURCES = {
    "eu_mdr": {
        "name": "EU MDR",
        "url": "https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en",
        "category": "EU MDR",
    },
    "team_nb": {
        "name": "Team-NB",
        "url": "https://www.team-nb.org/",
        "category": "Team-NB",
    },
    "fda": {
        "name": "FDA",
        "url": "https://www.fda.gov/medical-devices/",
        "rss_url": "https://www.fda.gov/medical-devices/rss.xml",
        "category": "FDA",
    },
    "imdrf": {
        "name": "IMDRF",
        "url": "https://www.imdrf.org/",
        "category": "IMDRF",
    },
    "nmpa": {
        "name": "NMPA",
        "url": "https://www.nmpa.gov.cn/ylqx/ylqxggtg/",
        "category": "NMPA",
    },
    "cmde": {
        "name": "CMDE器审中心",
        "url": "https://www.cmde.org.cn/flfg/zdyz/",
        "category": "CMDE",
    },
}


class UpdateChecker:
    def __init__(self):
        self.state = self._load_state()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Regulatory-Newsletter-Bot/1.0)"
        })
        self.updates = []
    
    def _load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def check_rss(self, source_id, source):
        """RSS 抓取 - 用于 FDA"""
        import xml.etree.ElementTree as ET
        from email.utils import parsedate_to_datetime
        
        url = source.get("rss_url")
        if not url:
            return None
            
        last_checked = self.state.get(source_id, {}).get("last_checked")
        
        try:
            resp = self.session.get(url, timeout=15)
            root = ET.fromstring(resp.content)
            
            new_items = []
            for item in root.findall(".//item")[:10]:
                pub_date = item.find("pubDate")
                title = item.find("title")
                link = item.find("link")
                
                # 检查是否为新内容
                if pub_date is not None and last_checked:
                    try:
                        pub_dt = parsedate_to_datetime(pub_date.text)
                        check_dt = datetime.fromisoformat(last_checked)
                        if pub_dt <= check_dt:
                            continue
                    except:
                        pass
                
                new_items.append({
                    "title": title.text if title is not None else "Unknown",
                    "link": link.text if link is not None else "",
                    "date": pub_date.text[:10] if pub_date is not None else ""
                })
            
            self.state[source_id] = {
                "last_checked": datetime.now().isoformat()
            }
            
            if new_items:
                return {
                    "source": source["name"],
                    "category": source["category"],
                    "new_items": new_items,
                    "count": len(new_items)
                }
            return None
            
        except Exception as e:
            print(f"  RSS Error: {e}")
            return None
    
    def check_webpage(self, source_id, source):
        """网页抓取 - 用于大部分来源"""
        url = source["url"]
        prev_titles = set(self.state.get(source_id, {}).get("titles", []))
        
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # 提取文章标题（通用逻辑，可能需要针对具体网站调整）
            titles = []
            links = {}
            
            # 尝试常见的文章链接选择器
            for tag in soup.find_all(["a", "h2", "h3", "h4"]):
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                
                # 过滤条件
                if len(title) < 10 or len(title) > 100:
                    continue
                if title in titles:
                    continue
                    
                titles.append(title)
                if href and not href.startswith("javascript"):
                    # 处理相对链接
                    if href.startswith("/"):
                        from urllib.parse import urljoin
                        href = urljoin(url, href)
                    links[title] = href
            
            # 找出新标题
            new_items = []
            for t in titles[:20]:
                if t not in prev_titles and prev_titles:  # 有历史记录时才算"新"
                    new_items.append({
                        "title": t,
                        "link": links.get(t, url),
                        "date": ""
                    })
            
            # 保存当前状态
            self.state[source_id] = {
                "url": url,
                "last_checked": datetime.now().isoformat(),
                "titles": titles[:50]
            }
            
            if new_items and prev_titles:
                return {
                    "source": source["name"],
                    "category": source["category"],
                    "new_items": new_items[:5],  # 只取前5条
                    "count": len(new_items)
                }
            elif not prev_titles:
                print(f"  -> 首次运行，建立基线（{len(titles)} 条标题）")
            return None
            
        except Exception as e:
            print(f"  Web Error: {e}")
            return None
    
    def check_source(self, source_id, source):
        """根据来源类型选择检查方式"""
        print(f"Checking {source['name']}...")
        
        if "rss_url" in source:
            result = self.check_rss(source_id, source)
        else:
            result = self.check_webpage(source_id, source)
        
        if result:
            print(f"  -> 发现 {result['count']} 条更新")
            self.updates.append(result)
        else:
            print(f"  -> 暂无更新")
        
        return result
    
    def check_all(self):
        """检查所有来源"""
        print(f"\n{'='*50}")
        print(f"开始查新：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}\n")
        
        for source_id, source in SOURCES.items():
            self.check_source(source_id, source)
        
        self._save_state()
        
        print(f"\n{'='*50}")
        print(f"查新完成：共 {len(self.updates)} 个来源有更新")
        print(f"{'='*50}")
        
        return self.updates
    
    def generate_report(self):
        """生成 JSON 报告"""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "updates": self.updates,
            "total_updates": sum(u.get("count", 0) for u in self.updates),
            "summary": (
                f"本周发现 {len(self.updates)} 个来源有更新，"
                f"共 {sum(u.get('count', 0) for u in self.updates)} 条"
                if self.updates else "本周暂无更新"
            )
        }


def main():
    checker = UpdateChecker()
    updates = checker.check_all()
    report = checker.generate_report()
    
    # 保存报告
    report_file = ROOT / "data" / f"report_{datetime.now().strftime('%Y%m%d')}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_file}")
    print(report["summary"])
    
    # 如果有更新，返回退出码 1（用于 GitHub Actions 条件判断）
    if updates:
        sys.exit(1)


if __name__ == "__main__":
    main()
