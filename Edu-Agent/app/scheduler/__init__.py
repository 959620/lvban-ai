"""
调度模块：APScheduler 进程内定时扫描到期提醒。

设计原因：
- MVP 与 API 同进程，部署简单
- 通过 settings.scheduler_enabled 可关闭，便于本地调试
- 生产环境可拆独立进程，而不改 ReminderService 接口
"""
