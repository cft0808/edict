"""Task 模型 — 三省六部任务核心表。

对应当前 tasks_source.json 中的每一条任务记录。
state 对应三省六部流转状态机：
  Taizi → Zhongshu → Menxia → Assigned → Doing → Review → Done
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Index,
    String,
    Text,
    Boolean,
    Integer,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from ..db import Base


class TaskState(str, enum.Enum):
    """任务状态枚举 — 映射三省六部流程。"""
    Taizi = "Taizi"           # 太子分拣
    Zhongshu = "Zhongshu"     # 中书省起草
    Menxia = "Menxia"         # 门下省审议
    Assigned = "Assigned"     # 尚书省已将任务派发
    Next = "Next"             # 待执行
    Doing = "Doing"           # 六部执行中
    Review = "Review"         # 审查汇总
    Done = "Done"             # 完成
    Blocked = "Blocked"       # 阻塞
    Cancelled = "Cancelled"   # 取消
    Pending = "Pending"       # 待处理


# 终态集合
TERMINAL_STATES = {TaskState.Done, TaskState.Cancelled}

# 状态流转合法路径
STATE_TRANSITIONS = {
    TaskState.Taizi: {TaskState.Zhongshu, TaskState.Cancelled},
    TaskState.Zhongshu: {TaskState.Menxia, TaskState.Cancelled, TaskState.Blocked},
    TaskState.Menxia: {TaskState.Assigned, TaskState.Zhongshu, TaskState.Cancelled},  # 封驳退回中书
    TaskState.Assigned: {TaskState.Doing, TaskState.Next, TaskState.Cancelled, TaskState.Blocked},
    TaskState.Next: {TaskState.Doing, TaskState.Cancelled},
    TaskState.Doing: {TaskState.Review, TaskState.Done, TaskState.Blocked, TaskState.Cancelled},
    TaskState.Review: {TaskState.Done, TaskState.Doing, TaskState.Cancelled},  # 审查不通过退回
    TaskState.Blocked: {TaskState.Taizi, TaskState.Zhongshu, TaskState.Menxia, TaskState.Assigned, TaskState.Doing},
}

# 状态 → Agent 映射
STATE_AGENT_MAP = {
    TaskState.Taizi: "taizi",
    TaskState.Zhongshu: "zhongshu",
    TaskState.Menxia: "menxia",
    TaskState.Assigned: "shangshu",
    TaskState.Review: "shangshu",
}

# 组织 → Agent 映射（六部）
ORG_AGENT_MAP = {
    "户部": "hubu",
    "礼部": "libu",
    "兵部": "bingbu",
    "刑部": "xingbu",
    "工部": "gongbu",
    "吏部": "libu_hr",
}


class Task(Base):
    """三省六部任务表。"""
    __tablename__ = "tasks"

    id = Column(String(32), primary_key=True, comment="任务ID, e.g. JJC-20260301-001")
    title = Column(Text, nullable=False, comment="任务标题")
    state = Column(Enum(TaskState, name="task_state"), nullable=False, default=TaskState.Taizi, index=True)
    org = Column(String(32), nullable=False, default="太子", comment="当前执行部门")
    official = Column(String(32), default="", comment="责任官员")
    now = Column(Text, default="", comment="当前进展描述")
    eta = Column(String(64), default="-", comment="预计完成时间")
    block = Column(Text, default="无", comment="阻塞原因")
    output = Column(Text, default="", comment="最终产出")
    priority = Column(String(16), default="normal", comment="优先级")
    archived = Column(Boolean, default=False, index=True)

    # JSONB 灵活字段
    flow_log = Column(JSONB, default=list, comment="流转日志 [{at, from, to, remark}]")
    progress_log = Column(JSONB, default=list, comment="进展日志 [{at, agent, text, todos}]")
    todos = Column(JSONB, default=list, comment="子任务 [{id, title, status, detail}]")
    scheduler = Column(JSONB, default=dict, comment="调度器元数据")
    template_id = Column(String(64), default="", comment="模板ID")
    template_params = Column(JSONB, default=dict, comment="模板参数")
    meta = Column(JSONB, default=dict, comment="元数据")
    ac = Column(Text, default="", comment="验收标准")
    target_dept = Column(String(64), default="", comment="目标部门")

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_tasks_state_archived", "state", "archived"),
        Index("ix_tasks_updated_at", "updated_at"),
    )

    def to_dict(self) -> dict:
        """序列化为 API 响应格式（兼容旧 live_status 格式）。"""
        return {
            "id": self.id,
            "title": self.title,
            "state": self.state.value if self.state else "",
            "org": self.org,
            "official": self.official,
            "now": self.now,
            "eta": self.eta,
            "block": self.block,
            "output": self.output,
            "priority": self.priority,
            "archived": self.archived,
            "flow_log": self.flow_log or [],
            "progress_log": self.progress_log or [],
            "todos": self.todos or [],
            "templateId": self.template_id,
            "templateParams": self.template_params or {},
            "ac": self.ac,
            "targetDept": self.target_dept,
            "scheduler": self.scheduler or {},
            "createdAt": self.created_at.isoformat() if self.created_at else "",
            "meta": self.meta or {},
            "updatedAt": self.updated_at.isoformat() if self.updated_at else "",
        }
