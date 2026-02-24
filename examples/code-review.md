# 案例 2：代码安全审查

> **旨意**：审查一段 FastAPI 代码的安全性，输出问题清单和修复建议

---

## 📜 圣旨（原始指令）

```
审查以下 FastAPI 代码的安全性，重点关注：
1. 认证与授权漏洞
2. SQL 注入风险
3. 输入验证
4. 敏感信息泄露
给出问题清单（按严重性排序）和修复代码。

[附件：app/main.py, app/models.py, app/auth.py — 合计 320 行]
```

**旨意 ID**：`JJC-20260221-007`
**下旨时间**：2026-02-21 14:30:00

---

## 📋 中书省规划

> 接旨后 30 秒内完成规划

**规划方案：**

| # | 子任务 | 派发部门 | 说明 |
|---|--------|----------|------|
| 1 | 代码安全扫描 | ⚔️ 兵部 | 逐文件审查，标记安全问题 |
| 2 | 合规与最佳实践检查 | ⚖️ 刑部 | 对照 OWASP Top 10 检查合规性 |
| 3 | 修复方案输出 | ⚔️ 兵部 | 针对每个问题给出修复代码 |

**预计耗时**：12 分钟
**预计 Token**：~9,000

---

## 🔍 门下省审议

> ⏱️ 审议耗时 18 秒

### 准奏 ✅（首轮通过）

**门下省批语：** *"方案合理。兵部负责工程侧审查，刑部负责合规侧审查，分工明确。注意刑部需出具 OWASP 逐项对照表，不能只写'基本合规'。准奏。"*

---

## ⚔️ 各部执行结果

### 兵部 · 代码安全扫描（耗时 5 分钟）

**扫描发现 6 个问题：**

| # | 严重性 | 文件 | 问题 |
|---|--------|------|------|
| 1 | 🔴 严重 | auth.py:23 | JWT secret 硬编码在源码中 |
| 2 | 🔴 严重 | main.py:45 | SQL 查询使用 f-string 拼接，存在注入风险 |
| 3 | 🟠 高危 | main.py:67 | 用户输入未做长度限制，可造成 DoS |
| 4 | 🟠 高危 | auth.py:41 | Token 过期时间设为 30 天，过长 |
| 5 | 🟡 中危 | main.py:12 | CORS 设置为 `allow_origins=["*"]` |
| 6 | 🟡 中危 | models.py:8 | 密码字段未排除在 response_model 之外 |

### 刑部 · OWASP 合规检查（耗时 4 分钟）

**OWASP Top 10 逐项对照：**

| OWASP 编号 | 类别 | 状态 | 说明 |
|-----------|------|------|------|
| A01 | Broken Access Control | 🟠 部分合规 | 有 JWT 但缺少角色粒度校验 |
| A02 | Cryptographic Failures | 🔴 不合规 | Secret 硬编码 |
| A03 | Injection | 🔴 不合规 | SQL 拼接 |
| A04 | Insecure Design | ✅ 合规 | 整体架构合理 |
| A05 | Security Misconfiguration | 🟡 需改进 | CORS 过宽 |
| A06 | Vulnerable Components | ✅ 合规 | 依赖版本较新 |
| A07 | Auth Failures | 🟠 部分合规 | Token 过期时间过长 |
| A08 | Data Integrity | ✅ 合规 | — |
| A09 | Logging Failures | 🟡 需改进 | 缺少安全事件日志 |
| A10 | SSRF | ✅ 合规 | 无外部请求 |

**刑部结论：** 6/10 项需要处理，其中 2 项不合规（A02、A03），需立即修复。

### 兵部 · 修复代码（耗时 3 分钟）

```python
# 修复 #1: auth.py — JWT secret 从环境变量读取
import os
JWT_SECRET = os.environ["JWT_SECRET"]  # 不再硬编码

# 修复 #2: main.py — 使用参数化查询
from sqlalchemy import text
result = db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})

# 修复 #3: main.py — 添加输入长度限制
from pydantic import Field
class UserInput(BaseModel):
    name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)

# 修复 #4: auth.py — 缩短 Token 过期时间
ACCESS_TOKEN_EXPIRE = timedelta(hours=1)  # 从 30 天改为 1 小时

# 修复 #5: main.py — 收紧 CORS
app.add_middleware(CORSMiddleware, allow_origins=["https://yourdomain.com"])

# 修复 #6: models.py — 密码字段排除
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    # password 字段不在此 model 中
```

---

## 📮 最终奏折（尚书省汇总）

**奏折 ID**：`JJC-20260221-007`
**总耗时**：14 分钟（规划 1 + 审议 0.5 + 执行 12.5）
**总 Token**：8,200

### 执行摘要

对 320 行 FastAPI 代码完成安全审查。发现 6 个安全问题（2 严重 / 2 高危 / 2 中危），OWASP Top 10 中有 2 项不合规。已提供全部 6 个问题的修复代码。

门下省首轮即准奏，兵部和刑部分工明确：兵部负责代码层面扫描和修复，刑部负责合规框架对照。

### 建议优先级

1. **立即修复**：JWT secret 硬编码 + SQL 注入（上线前必须解决）
2. **本周内**：输入长度限制 + Token 过期时间
3. **下个迭代**：CORS 收紧 + 密码字段暴露

---

*本案例基于真实运行记录整理，代码内容已脱敏。*
