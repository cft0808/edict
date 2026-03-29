# active_meditation_trigger.py — 主动沉思触发器

## 概述
v1.3 主动沉思触发脚本。运行在内务巡查之后，检查是否需要触发主动沉思。

## 核心功能
- `check`：主检查流程，检测所有触发条件
- `trigger <type>`：手动触发指定类型的沉思

## 触发条件

### 1. 规律重复触发
- 检查 `memory/patterns/repeating_issues.json`
- count >= 3 → 触发根因挖掘

### 2. 工具异常触发
- 检查 `memory/reflections/tool-issues.md`
- 发现新的系统性异常 → 触发分析

### 3. 皇上不满触发（待实现）
- 需要聊天历史输入
- 目前是占位符

### 4. 定时触发
- 周沉思：周日 22:00-23:59
- 月沉思：每月最后一天 22:00-23:59

## 输出
触发记录写入 `memory/reflections/active_triggers/<type>_<timestamp>.md`

## 集成
由 `hourly_housekeeping.py` 或 `nightly_meditation.py` 调用。

## 版本
v1.0 — 2026-03-30
