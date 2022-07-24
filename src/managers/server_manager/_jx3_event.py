import time
from abc import abstractmethod
from datetime import datetime
from typing import Literal, Optional

from nonebot.adapters import Event as BaseEvent
from nonebot.adapters.onebot.v11.message import Message
from nonebot.typing import overrides
from nonebot.utils import escape_tag
from pydantic import BaseModel


class EventRister:
    """事件注册器"""

    event_dict: dict[int, "RecvEvent"] = {}
    """事件映射字典"""

    @classmethod
    def rister(cls, action: int) -> "RecvEvent":
        def _rister(event):
            cls.event_dict[action] = event
            return event

        return _rister

    @classmethod
    def get_event(cls, ws_data: "WsData") -> Optional["RecvEvent"]:
        event = cls.event_dict.get(ws_data.action)
        if event:
            return event(ws_data.data)
        return None


class WsData(BaseModel):
    """
    ws数据模型
    """

    action: int
    """ws消息类型"""
    data: dict
    """消息数据"""


class WsNotice(BaseEvent):
    """ws通知主人事件"""

    __event__ = "WsNotice"
    post_type: str = "WsNotice"
    message: str = ""
    """通知内容"""

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    @overrides(BaseEvent)
    def get_type(self) -> str:
        return self.post_type

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        return self.post_type

    @overrides(BaseEvent)
    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    @overrides(BaseEvent)
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_plaintext(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_user_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_session_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def is_tome(self) -> bool:
        return False


class RecvEvent(BaseEvent):
    """ws推送事件"""

    __event__ = "WsRecv"
    post_type: str = "WsRecv"
    message_type: str
    action: int
    """ws消息类型"""
    server: Optional[str] = None
    """影响服务器"""

    @property
    @abstractmethod
    def log(self) -> str:
        """事件日志内容"""
        raise NotImplementedError

    @overrides(BaseEvent)
    def get_type(self) -> str:
        return self.post_type

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        message_type = getattr(self, "message_type", None)
        return f"{self.post_type}" + (f".{message_type}" if message_type else "")

    @overrides(BaseEvent)
    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    @overrides(BaseEvent)
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_plaintext(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_user_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_session_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def is_tome(self) -> bool:
        return False


@EventRister.rister(action=2001)
class ServerStatusEvent(RecvEvent):
    """服务器状态推送事件"""

    __event__ = "WsRecv.ServerStatus"
    message_type = "ServerStatus"
    status: bool
    """服务器状态"""

    def __init__(self, data: dict):
        """
        服务器状态推送事件
        """
        super().__init__()
        self.server = data.get("server")
        status = data.get("status")
        self.status = True if status == 1 else False

    @property
    def log(self) -> str:
        if self.status == 1:
            status = "已开服"
        else:
            status = "已维护"
        log = f"开服推送事件：[{self.server}]状态-{status}"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        time_now = datetime.now().strftime("%H时%M分")
        if self.status:
            return Message(f"时间：{time_now}\n[{self.server}] 开服啦！")
        else:
            return Message(f"时间{time_now}\n[{self.server}]维护惹。")


@EventRister.rister(action=2002)
class NewsRecvEvent(RecvEvent):
    """新闻推送事件"""

    __event__ = "WsRecv.News"
    message_type = "News"
    news_type: str
    """新闻类型"""
    news_tittle: str
    """新闻标题"""
    news_url: str
    """新闻url链接"""
    news_date: str
    """新闻日期"""

    def __init__(self, data: dict):
        """
        新闻推送事件
        """
        super().__init__()
        self.news_type = data.get("type")
        self.news_tittle = data.get("title")
        self.news_url = data.get("url")
        self.news_date = data.get("date")

    @property
    def log(self) -> str:
        log = f"[{self.news_type}]事件：{self.news_tittle}"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(
            f"[{self.news_type}]来惹\n标题：{self.news_tittle}\n链接：{self.news_url}\n日期：{self.news_date}"
        )


@EventRister.rister(action=1001)
class SerendipityEvent(RecvEvent):
    """奇遇播报事件"""

    __event__ = "WsRecv.Serendipity"
    message_type = "Serendipity"
    name: str
    """触发角色"""
    serendipity: str
    """奇遇名"""
    level: int
    """奇遇等级"""
    time: str
    """触发时间"""

    def __init__(self, data: dict):
        """
        奇遇播报事件
        """
        super().__init__()
        self.server = data.get("server")
        self.name = data.get("name")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%m/%d %H:%M", start_trans)
        self.serendipity = data.get("serendipity")
        self.level = data.get("level")

    @property
    def log(self) -> str:
        log = f"奇遇推送事件：[{self.server}]的[{self.name}]抱走了奇遇：{self.serendipity}"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(f"奇遇推送 {self.time}\n{self.serendipity} 被 {self.name} 抱走惹。")


@EventRister.rister(action=1002)
class HorseRefreshEvent(RecvEvent):
    """马驹刷新事件"""

    __event__ = "WsRecv.HorseRefresh"
    message_type = "HorseRefresh"
    map: str
    """刷新地图"""
    min: int
    """时间范围min"""
    max: int
    """时间范围max"""
    time: str
    """推送时间"""

    def __init__(self, data: dict):
        """
        马驹刷新事件
        """
        super().__init__()
        self.server = data.get("server")
        self.map = data.get("map")
        self.min = data.get("min")
        self.max = data.get("max")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%H:%M:%S", start_trans)

    @property
    def log(self) -> str:
        log = f"马驹刷新推送：[{self.server}]的[{self.map}]将要在 {str(self.min)}-{str(self.max)} 分后刷新马驹。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(
            f"[抓马监控] 时间：{self.time}\n{self.map} 将在[{self.min} - {self.max}分]后刷新马驹。"
        )


@EventRister.rister(action=1003)
class HorseCatchedEvent(RecvEvent):
    """马驹捕获事件"""

    __event__ = "WsRecv.HorseCatched"
    message_type = "HorseCatched"
    name: str
    """触发角色名"""
    map: str
    """地图"""
    horse: str
    """马驹名"""
    time: str
    """事件时间"""

    def __init__(self, data: dict):
        """
        马驹捕获事件
        """
        super().__init__()
        self.server = data.get("server")
        self.map = data.get("map")
        self.name = data.get("name")
        self.horse = data.get("horse")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%H:%M:%S", start_trans)

    @property
    def log(self) -> str:
        log = f"马驹被抓事件：[{self.server}]的[{self.name}]在[{self.map}]捕获了 {self.horse} 。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(
            f"[抓马监控] 时间：{self.time}\n{self.map} 的 {self.horse} 被 {self.name} 抓走了~"
        )


@EventRister.rister(action=1004)
class FuyaoRefreshEvent(RecvEvent):
    """扶摇开启事件"""

    __event__ = "WsRecv.FuyaoRefresh"
    message_type = "FuyaoRefresh"
    time: str
    """事件时间"""

    def __init__(self, data: dict):
        """
        扶摇开启事件
        """
        super().__init__()
        self.server = data.get("server")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%H:%M:%S", start_trans)

    @property
    def log(self) -> str:
        log = f"扶摇刷新事件：[{self.server}]的扶摇开始刷新 。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(f"[扶摇监控]\n扶摇九天在 {self.time} 开启了。")


@EventRister.rister(action=1005)
class FuyaoNamedEvent(RecvEvent):
    """扶摇点名事件"""

    __event__ = "WsRecv.FuyaoNamed"
    message_type = "FuyaoNamed"
    names: list[str]
    """点名角色组"""
    time: str
    """点名时间"""

    def __init__(self, data: dict):
        """
        扶摇点名事件
        """
        super().__init__()
        self.server = data.get("server")
        self.names = data.get("name")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%H:%M:%S", start_trans)

    @property
    def log(self) -> str:
        name = ",".join(self.names)
        log = f"扶摇点名事件：[{self.server}]的扶摇点名了，玩家[{name}] 。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        name = ",".join(self.names)
        return Message(f"[扶摇监控] 时间：{self.time}\n唐文羽点名了[{name}]。")


@EventRister.rister(action=1006)
class FireworksEvent(RecvEvent):
    """烟花播报事件"""

    __event__ = "WsRecv.Fireworks"
    message_type = "Fireworks"
    role: str
    """烟花地图"""
    name: str
    """接受烟花的角色"""
    sender: str
    """使用烟花的角色"""
    recipient: str
    """烟花名字"""
    time: str
    """烟花使用时间"""

    def __init__(self, data: dict):
        """
        烟花播报事件
        """
        super().__init__()
        self.server = data.get("server")
        self.map = data.get("map")
        self.name = data.get("name")
        self.sender = data.get("sender")
        self.recipient = data.get("recipient")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%H:%M:%S", start_trans)

    @property
    def log(self) -> str:
        log = f"烟花事件：{self.sender} 在 {self.map} 对 {self.name} 使用了烟花：{self.recipient}。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(
            f"[烟花监控] 时间：{self.time}\n{self.sender} 在 {self.map} 对 {self.name} 使用了烟花：{self.recipient}。"
        )


@EventRister.rister(action=1007)
class XuanJingEvent(RecvEvent):
    """玄晶获取事件"""

    __event__ = "WsRecv.XuanJing"
    message_type = "XuanJing"
    role: str
    """角色名"""
    map: str
    """地图名"""
    name: str
    """玄晶名"""
    time: str
    """获取时间"""

    def __init__(self, data: dict):
        """
        玄晶获取事件
        """
        super().__init__()
        self.server = data.get("server")
        self.map = data.get("map")
        self.name = data.get("name")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%H:%M:%S", start_trans)

    @property
    def log(self) -> str:
        log = f"玄晶事件：[{self.time}] 侠士 {self.role} 在 {self.map} 获取了 {self.name}。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(
            f"[玄晶监控] 时间：{self.time}\n侠士 {self.role} 在 {self.map} 获取了 {self.name}！"
        )


@EventRister.rister(action=1008)
class GameSysMsgEvent(RecvEvent):
    """游戏系统频道消息推送"""

    __event__ = "WsRecv.GameSysMsg"
    message_type = "GameSysMsg"
    message: Optional[str]
    """消息内容"""
    time: Optional[str]
    """消息时间"""

    def __init__(self, data: dict):
        """游戏系统频道消息推送"""
        super().__init__()
        self.server = data.get("server")
        get_time = int(data.get("time"))
        start_trans = time.localtime(get_time)
        self.time = time.strftime("%H:%M:%S", start_trans)

    @property
    def log(self) -> str:
        log = f"系统频道推送：{self.message}。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(f"[系统频道推送]\n时间：{self.time}\n{self.message}。")


@EventRister.rister(action=10001)
class SubscribeEvent(RecvEvent):
    """订阅回执"""

    __event__ = "WsRecv.Subscribe"
    message_type = "Subscribe"
    action: Literal["烟花报时", "玄晶报时", "游戏消息"]
    """订阅内容"""
    server_dict: dict[str, int]
    """已订阅服务器"""

    def __init__(self, data: dict):
        """订阅回执"""
        super().__init__()
        action = data.get("action")
        match action:
            case 1006:
                self.action = "烟花报时"
            case 1007:
                self.action = "玄晶报时"
            case 1010:
                self.action = "游戏消息"
        self.server_dict = data.get("server")

    @property
    def log(self) -> str:
        log = f"订阅回执，类型：{self.action}。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(f"[订阅回执]\n类型：{self.action}。")


@EventRister.rister(action=10002)
class DisSubscribeEvent(RecvEvent):
    """取消订阅回执"""

    __event__ = "WsRecv.DisSubscribe"
    message_type = "DisSubscribe"
    action: Literal["烟花报时", "玄晶报时", "游戏消息"]
    """订阅内容"""
    server_dict: dict[str, int]
    """已订阅服务器"""

    def __init__(self, data: dict):
        """取消订阅回执"""
        super().__init__()
        action = data.get("action")
        match action:
            case 1006:
                self.action = "烟花报时"
            case 1007:
                self.action = "玄晶报时"
            case 1010:
                self.action = "游戏消息"
        self.server_dict = data.get("server")

    @property
    def log(self) -> str:
        log = f"取消订阅回执，类型：{self.action}。"
        return log

    @overrides(RecvEvent)
    def get_message(self) -> Message:
        return Message(f"[取消订阅回执]\n类型：{self.action}。")
