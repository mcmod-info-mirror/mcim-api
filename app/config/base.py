import os
import json
import logging
from typing import TypeVar, Generic, Type, Optional, Tuple, Dict, Any, Union
from pydantic import BaseModel, ValidationError

# 设置日志
logger = logging.getLogger(__name__)

# 泛型类型变量，表示任何继承自 BaseModel 的类型
T = TypeVar("T", bound=BaseModel)


class BaseConfig(Generic[T]):
    """
    通用配置基类，提供配置的加载、保存和验证功能
    子类需要指定 MODEL_CLASS 和 DEFAULT_CONFIG_PATH
    """

    MODEL_CLASS: Type[T] = None  # 配置模型类
    DEFAULT_CONFIG_PATH: str = None  # 默认配置文件路径

    @classmethod
    def save(cls, model: Optional[T] = None, target: Optional[str] = None) -> None:
        """
        保存配置到文件

        Args:
            model: 配置模型实例，如果为None则创建一个默认实例
            target: 目标文件路径，如果为None则使用默认路径
        """
        if cls.MODEL_CLASS is None:
            raise NotImplementedError("子类必须指定 MODEL_CLASS")

        if target is None:
            if cls.DEFAULT_CONFIG_PATH is None:
                raise NotImplementedError(
                    "子类必须指定 DEFAULT_CONFIG_PATH 或提供 target 参数"
                )
            target = cls.DEFAULT_CONFIG_PATH

        if model is None:
            model = cls.MODEL_CLASS()

        # 确保目录存在
        os.makedirs(os.path.dirname(target), exist_ok=True)

        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @classmethod
    def load(cls, target: Optional[str] = None) -> T:
        """
        从文件加载配置

        Args:
            target: 配置文件路径，如果为None则使用默认路径

        Returns:
            配置模型实例
        """
        if cls.MODEL_CLASS is None:
            raise NotImplementedError("子类必须指定 MODEL_CLASS")

        if target is None:
            if cls.DEFAULT_CONFIG_PATH is None:
                raise NotImplementedError(
                    "子类必须指定 DEFAULT_CONFIG_PATH 或提供 target 参数"
                )
            target = cls.DEFAULT_CONFIG_PATH

        if not os.path.exists(target):
            cls.save(target=target)
            return cls.MODEL_CLASS()

        with open(target, "r") as fd:
            data = json.load(fd)

        return cls.MODEL_CLASS(**data)

    @classmethod
    def validate(cls, target: Optional[str] = None) -> Tuple[bool, str, Optional[T]]:
        """
        验证配置文件是否可以正确加载和解析

        Args:
            target: 配置文件路径，如果为None则使用默认路径

        Returns:
            Tuple[bool, str, Optional[T]]:
                - 第一个元素：配置文件是否有效
                - 第二个元素：错误信息（如果有）
                - 第三个元素：成功加载的配置实例（如果加载成功）
        """
        if cls.MODEL_CLASS is None:
            return False, "子类必须指定 MODEL_CLASS", None

        if target is None:
            if cls.DEFAULT_CONFIG_PATH is None:
                return (
                    False,
                    "子类必须指定 DEFAULT_CONFIG_PATH 或提供 target 参数",
                    None,
                )
            target = cls.DEFAULT_CONFIG_PATH

        # 检查文件是否存在
        if not os.path.exists(target):
            return False, f"配置文件不存在: {target}", None

        try:
            # 尝试读取文件
            with open(target, "r") as fd:
                try:
                    # 尝试解析JSON
                    data = json.load(fd)
                except json.JSONDecodeError as e:
                    return False, f"无效的JSON格式: {str(e)}", None

                try:
                    # 尝试创建配置模型实例
                    config = cls.MODEL_CLASS(**data)
                    return True, "", config
                except ValidationError as e:
                    return False, f"配置验证失败: {str(e)}", None
                except Exception as e:
                    return False, f"创建配置实例时出错: {str(e)}", None

        except IOError as e:
            return False, f"无法读取配置文件: {str(e)}", None
        except Exception as e:
            return False, f"验证配置时出错: {str(e)}", None

    @classmethod
    def is_valid(cls, target: Optional[str] = None) -> bool:
        """
        快速检查配置文件是否有效

        Args:
            target: 配置文件路径，如果为None则使用默认路径

        Returns:
            bool: 配置文件是否有效
        """
        is_valid, _, _ = cls.validate(target)
        return is_valid
