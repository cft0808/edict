#!/usr/bin/env python3
"""
Active Meditation Trigger — v1.3 主动沉思触发脚本

运行在 hourly_housekeeping 之后，检查是否需要触发主动沉思。

触发条件：
1. 规律重复触发：同一类型问题出现 3 次
2. 工具异常触发：tool-issues.md 中有新的异常
3.皇上不满触发：检测到皇上语气不满的关键词
4. 周/月度定时沉思：周日晚上或每月最后一天

输出：
- 触发记录写入 memory/reflections/active_triggers/
- 如果是突破性洞察，生成行动项

用法：
  python3 scripts/active_meditation_trigger.py check
  python3 scripts/active_meditation_trigger.py trigger <type>
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

MEMORY_HOURLY = Path(__file__).parent.parent / "memory" / "hourly"
MEMORY_REFLECTIONS = Path(__file__).parent.parent / "memory" / "reflections"
MEMORY_PATTERNS = Path(__file__).parent.parent / "memory" / "patterns"
MEMORY_TOOL_ISSUES = MEMORY_REFLECTIONS / "tool-issues.md"
TRIGGERS_DIR = MEMORY_REFLECTIONS / "active_triggers"


def ensure_dirs():
    """确保目录存在"""
    TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_PATTERNS.mkdir(parents=True, exist_ok=True)


def load_recent_reports():
    """加载最近的内务巡查报告"""
    reports = []
    if not MEMORY_HOURLY.exists():
        return reports
    
    # 获取最近 24 小时内的报告
    cutoff = datetime.now() - timedelta(hours=24)
    for f in sorted(MEMORY_HOURLY.glob("report_*.md"), reverse=True):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime > cutoff:
                content = f.read_text()
                reports.append({
                    "file": f.name,
                    "mtime": mtime,
                    "content": content
                })
        except:
            pass
    
    return reports


def load_tool_issues():
    """加载工具异常记录"""
    if not MEMORY_TOOL_ISSUES.exists():
        return []
    
    content = MEMORY_TOOL_ISSUES.read_text()
    issues = []
    
    # 简单的解析：提取 ## 开头的异常条目
    for line in content.split("\n"):
        if line.startswith("## "):
            issues.append(line.strip())
    
    return issues


def check_repeating_patterns():
    """检查规律重复问题"""
    # 读取 memory/patterns/ 下的重复问题索引
    pattern_file = MEMORY_PATTERNS / "repeating_issues.json"
    
    patterns = []
    if pattern_file.exists():
        try:
            patterns = json.loads(pattern_file.read_text()).get("issues", [])
        except:
            pass
    
    # 检查是否有 count >= 3 的问题
    critical = [p for p in patterns if p.get("count", 0) >= 3]
    
    return critical


def check_tool_anomalies():
    """检查工具异常"""
    issues = load_tool_issues()
    
    # 过滤出最近 24 小时的异常
    recent = []
    cutoff = datetime.now() - timedelta(hours=24)
    for issue in issues:
        # 简单处理：只返回所有异常，让调用方判断时间
        recent.append(issue)
    
    return recent


def is_scheduled_trigger():
    """检查是否应该触发定时沉思"""
    now = datetime.now()
    
    # 周沉思：周日 22:00-23:59
    if now.weekday() == 6 and now.hour >= 22:
        return ("weekly", f"周沉思 {now.strftime('%Y-%m-%d')}")
    
    # 月沉思：每月最后一天 22:00-23:59
    if now.day >= 28:  # 简化判断
        # 检查是否是月末
        next_month = now.replace(day=1) + timedelta(days=32)
        last_day = (next_month.replace(day=1) - timedelta(days=1)).day
        if now.day == last_day and now.hour >= 22:
            return ("monthly", f"月沉思 {now.strftime('%Y-%m')}")
    
    return None


def detect_user_frustration(chat_history=None):
    """检测皇上不满意的信号（启发式）"""
    # 如果有 chat_history，分析最近的消息
    # 简化：返回空列表，实际使用时需要传入消息内容
    return []


def write_trigger_record(trigger_type, content, is_breakthrough=False):
    """写入触发记录"""
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = TRIGGERS_DIR / f"{trigger_type}_{timestamp}.md"
    
    frontmatter = f"""---
trigger_type: {trigger_type}
is_breakthrough: {is_breakthrough}
created: {datetime.now().isoformat()}
---

"""
    filename.write_text(frontmatter + content)
    return filename


def generate_weekly_reflection(reports):
    """生成周沉思"""
    content = f"""# 周沉思 — {datetime.now().strftime('%Y-%m-%d')}

## 本周回顾

### 完成的重要任务
（臣回顾本周完成的 JJC 任务...）

### 最深刻的突破
（如果有突破性洞察...）

### 跳步最多的地方
（臣反思本周哪里做得不够...）

### 系统性改进机会
（发现了什么可以系统性解决的问题...）

## 下周计划

（臣对下周的重点判断...）

## 对皇上的提案（如有）
（如果有皇上应该知道的事...）
"""
    return content


def check():
    """主检查流程"""
    ensure_dirs()
    triggers_fired = []
    
    print("=== Active Meditation Trigger Check ===")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # 1. 检查规律重复
    print("1. 检查规律重复...")
    repeating = check_repeating_patterns()
    if repeating:
        print(f"   发现 {len(repeating)} 个重复问题（>=3次）")
        for p in repeating:
            print(f"   - {p.get('hash', 'unknown')}: {p.get('count', 0)}次")
            content = f"""# 规律重复触发

## 问题
{p.get('hash', 'unknown')}

## 出现次数
{p.get('count', 0)}次

## 最后出现
{p.get('last_seen', 'unknown')}

##臣的根因分析
（臣来挖根因...）

## 建议行动
（臣提出系统性的解决方案...）
"""
            write_trigger_record("repeating", content)
            triggers_fired.append("repeating")
    else:
        print("   无重复问题")
    
    print()
    
    # 2. 检查工具异常
    print("2. 检查工具异常...")
    anomalies = check_tool_anomalies()
    if anomalies:
        print(f"   发现 {len(anomalies)} 个工具异常")
        content = f"""# 工具异常触发

## 异常数量
{len(anomalies)} 个（最近）

## 异常列表
"""
        for a in anomalies[:5]:
            content += f"- {a}\n"
        
        content += """
##臣的分析
（臣来识别这些异常是系统性问题还是偶发问题...）

## 建议行动
- 如果是系统性问题：臣建议创建改进任务
- 如果是偶发问题：记录但不行动
"""
        write_trigger_record("tool_anomaly", content)
        triggers_fired.append("tool_anomaly")
    else:
        print("   无工具异常")
    
    print()
    
    # 3. 检查定时触发
    print("3. 检查定时沉思...")
    scheduled = is_scheduled_trigger()
    if scheduled:
        print(f"   触发：{scheduled[1]}")
        if scheduled[0] == "weekly":
            content = generate_weekly_reflection(load_recent_reports())
            write_trigger_record("scheduled_weekly", content)
            triggers_fired.append("scheduled_weekly")
    else:
        print("   不在定时沉思时间")
    
    print()
    
    # 总结
    if triggers_fired:
        print(f"=== 触发 {len(triggers_fired)} 个沉思 ===")
        for t in triggers_fired:
            print(f"  - {t}")
        print()
        print("触发记录已写入 memory/reflections/active_triggers/")
        print("请臣在下次运行时检查这些触发器，执行沉思流程。")
    else:
        print("无触发。")
    
    return triggers_fired


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    
    if cmd == "check":
        check()
    elif cmd == "trigger":
        trigger_type = sys.argv[2] if len(sys.argv) > 2 else "manual"
        write_trigger_record(trigger_type, f"# 手动触发沉思\n\n类型：{trigger_type}\n\n臣的反思：\n\n")
        print(f"已创建触发记录：{trigger_type}")
    else:
        print(__doc__)
