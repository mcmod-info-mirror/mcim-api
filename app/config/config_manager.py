# import os
# import threading
# import time
# from typing import Dict, Any, Set, Callable
# import logging

# # 使用同步版本的 watch
# from watchfiles import watch

# from app.config.constants import (
#     CONFIG_PATH,
#     MICM_CONFIG_PATH,
#     MONGODB_CONFIG_PATH,
#     REDIS_CONFIG_PATH,
# )
# from app.config.mcim import MCIMConfig, MCIMConfigModel
# from app.config.mongodb import MongodbConfig, MongodbConfigModel
# from app.config.redis import RedisConfig, RedisConfigModel

# logging.getLogger("watchfiles").setLevel(logging.WARNING)

# logger = logging.getLogger(__name__)


# class ConfigManager:
#     _instance = None

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(ConfigManager, cls).__new__(cls)
#             cls._instance._init()
#         return cls._instance

#     def _init(self):
#         # 初始化配置
#         self._mcim_config = MCIMConfig.load()
#         self._mongodb_config = MongodbConfig.load()
#         self._redis_config = RedisConfig.load()

#         # 监控的配置文件路径和加载函数的映射
#         self._config_paths = {
#             MICM_CONFIG_PATH: self._reload_mcim_config,
#             MONGODB_CONFIG_PATH: self._reload_mongodb_config,
#             REDIS_CONFIG_PATH: self._reload_redis_config,
#         }

#         # 配置变更回调函数注册表
#         self._change_callbacks: Dict[str, Set[Callable]] = {
#             MICM_CONFIG_PATH: set(),
#             MONGODB_CONFIG_PATH: set(),
#             REDIS_CONFIG_PATH: set(),
#         }

#         # 启动监控线程
#         self._should_stop = False
#         self._watcher_thread = threading.Thread(target=self._run_watcher, daemon=True, name="ConfigWatcher")
#         self._watcher_thread.start()

#         logger.info("ConfigManager initialized and watching for changes")

#     def _reload_mcim_config(self) -> None:
#         """重新加载MCIM配置"""
#         self._mcim_config = MCIMConfig.load()
#         logger.info("MCIM config reloaded")

#     def _reload_mongodb_config(self) -> None:
#         """重新加载MongoDB配置"""
#         self._mongodb_config = MongodbConfig.load()
#         logger.info("MongoDB config reloaded")

#     def _reload_redis_config(self) -> None:
#         """重新加载Redis配置"""
#         self._redis_config = RedisConfig.load()
#         logger.info("Redis config reloaded")

#     def _validate_config_file(self, config_path):
#         """
#         验证配置文件是否有效

#         Args:
#             config_path: 配置文件路径

#         Returns:
#             tuple: (is_valid, error_message) - 配置是否有效和错误信息
#         """
#         # 根据配置路径选择对应的配置类
#         config_class = None
#         if config_path == MICM_CONFIG_PATH:
#             config_class = MCIMConfig
#         elif config_path == MONGODB_CONFIG_PATH:
#             config_class = MongodbConfig
#         elif config_path == REDIS_CONFIG_PATH:
#             config_class = RedisConfig
#         else:
#             return False, f"未知的配置路径: {config_path}"

#         # 使用配置类的验证方法
#         is_valid, error_message, _ = config_class.validate(config_path)
#         return is_valid, error_message

#     def _run_watcher(self) -> None:
#         """在单独的线程中运行文件监控"""
#         # 确保CONFIG_PATH目录存在
#         if not os.path.exists(CONFIG_PATH):
#             os.makedirs(CONFIG_PATH)

#         # 根据环境选择最佳监控策略
#         force_polling = True  # 在 Windows 上强制使用轮询可能更稳定

#         while not self._should_stop:
#             try:
#                 # 使用同步版本的 watch 函数
#                 for changes in watch(
#                     CONFIG_PATH,
#                     watch_filter=lambda change, path: str(path).endswith(".json"),
#                     force_polling=force_polling,  # 强制使用轮询，更稳定
#                 ):
#                     if self._should_stop:
#                         break

#                     for change, path in changes:
#                         path = str(path).replace("\\", "/")  # 标准化路径
#                         for config_path, reload_func in self._config_paths.items():
#                             config_path = config_path.replace("\\", "/")  # 标准化路径
#                             if path.endswith(config_path.split("/")[-1]):
#                                 # 先验证配置文件是否有效
#                                 is_valid, error_message = self._validate_config_file(config_path)
#                                 if not is_valid:
#                                     logger.warning(f"检测到无效的配置文件修改: {os.path.basename(path)}, 错误: {error_message}")
#                                     continue  # 跳过无效的配置文件修改

#                                 # 重新加载配置
#                                 try:
#                                     reload_func()
#                                     logger.info(f"Reloaded config file: {os.path.basename(path)}")

#                                     # 调用注册的回调函数
#                                     for callback in self._change_callbacks.get(config_path, set()):
#                                         try:
#                                             # 处理异步回调
#                                             if hasattr(callback, "__code__") and callback.__code__.co_flags & 0x80:
#                                                 # 如果是异步函数，创建一个单独的线程来运行事件循环
#                                                 threading.Thread(
#                                                     target=self._run_async_callback,
#                                                     args=(callback,),
#                                                     daemon=True
#                                                 ).start()
#                                             else:
#                                                 # 同步函数直接调用
#                                                 callback()
#                                         except Exception as e:
#                                             logger.error(f"Error in config change callback: {e}")
#                                 except Exception as e:
#                                     logger.error(f"Failed to reload config {path}: {e}")

#             except KeyboardInterrupt:
#                 # 键盘中断优雅退出
#                 logger.info("Config watcher received keyboard interrupt")
#                 break
#             except Exception as e:
#                 logger.error(f"File watcher encountered an error: {e}")
#                 # 如果监控失败，等待5秒后重试
#                 time.sleep(5)
#                 # 继续循环，不退出监控

#         logger.info("Config file watcher stopped")

#     def _run_async_callback(self, callback):
#         """在单独的线程中运行异步回调"""
#         import asyncio
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             loop.run_until_complete(callback())
#         except Exception as e:
#             logger.error(f"Error running async callback: {e}")
#         finally:
#             loop.close()

#     def stop_watching(self):
#         """停止文件监控"""
#         self._should_stop = True
#         if self._watcher_thread.is_alive():
#             self._watcher_thread.join(timeout=2.0)
#         logger.info("Config file watcher stopped")

#     def register_change_callback(self, config_path: str, callback: Callable) -> None:
#         """注册配置变更的回调函数"""
#         if config_path in self._change_callbacks:
#             self._change_callbacks[config_path].add(callback)
#         else:
#             logger.warning(
#                 f"Attempted to register callback for unknown config path: {config_path}"
#             )

#     def unregister_change_callback(self, config_path: str, callback: Callable) -> None:
#         """取消注册配置变更的回调函数"""
#         if (
#             config_path in self._change_callbacks
#             and callback in self._change_callbacks[config_path]
#         ):
#             self._change_callbacks[config_path].remove(callback)

#     @property
#     def mcim_config(self) -> MCIMConfigModel:
#         """获取MCIM配置"""
#         return self._mcim_config

#     @property
#     def mongodb_config(self) -> MongodbConfigModel:
#         """获取MongoDB配置"""
#         return self._mongodb_config

#     @property
#     def redis_config(self) -> RedisConfigModel:
#         """获取Redis配置"""
#         return self._redis_config

#     def reload_all(self) -> None:
#         """强制重新加载所有配置"""
#         self._reload_mcim_config()
#         self._reload_mongodb_config()
#         self._reload_redis_config()


# # 全局配置管理器单例
# config_manager = ConfigManager()

import os
import threading
import time
from typing import Dict, Any, Set, Callable, Type, List, Tuple
import logging
from importlib import import_module
import inspect

# 使用同步版本的 watch
from watchfiles import watch

from app.config.base import BaseConfig
from app.config.constants import CONFIG_PATH

# 设置 watchfiles 日志级别为 WARNING，避免 DEBUG 消息
logging.getLogger("watchfiles").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        # 自动发现配置类
        self._config_registry = self._discover_config_classes()

        # 从配置类注册表构建配置路径映射
        self._config_paths = {}
        for config_name, config_class in self._config_registry.items():
            if (
                hasattr(config_class, "DEFAULT_CONFIG_PATH")
                and config_class.DEFAULT_CONFIG_PATH
            ):
                self._config_paths[config_class.DEFAULT_CONFIG_PATH] = (
                    config_name,
                    config_class,
                )

        # 配置实例缓存
        self._config_instances = {}

        # 初始加载所有配置
        self._load_all_configs()

        # 配置变更回调函数注册表
        self._change_callbacks: Dict[str, Set[Callable]] = {
            path: set() for path in self._config_paths.keys()
        }

        # 启动监控线程
        self._should_stop = False
        self._watcher_thread = threading.Thread(target=self._run_watcher, daemon=True, name="ConfigWatcher")
        self._watcher_thread.start()

        logger.info("ConfigManager initialized and watching for changes")
        logger.info(f"Monitoring config paths: {list(self._config_paths.keys())}")

    def _discover_config_classes(self) -> Dict[str, Type[BaseConfig]]:
        """
        自动发现项目中的所有配置类

        Returns:
            Dict[str, Type[BaseConfig]]: 配置名称到配置类的映射
        """
        config_classes = {}

        # 定义要扫描的模块列表
        modules_to_scan = [
            "app.config.mcim",
            "app.config.mongodb",
            "app.config.redis",
            # 可以添加更多模块路径
        ]

        for module_path in modules_to_scan:
            try:
                module = import_module(module_path)

                # 查找模块中的所有Config子类
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseConfig)
                        and obj != BaseConfig
                    ):
                        # 获取配置名称（去掉Config后缀）
                        config_name = name.replace("Config", "").lower()
                        config_classes[config_name] = obj
                        logger.debug(f"Discovered config class: {name}")

            except (ImportError, AttributeError) as e:
                logger.warning(f"Error scanning module {module_path}: {e}")

        return config_classes

    def _load_all_configs(self):
        """初始加载所有配置"""
        for config_name, config_class in self._config_registry.items():
            try:
                self._config_instances[config_name] = config_class.load()
                logger.info(f"Loaded config: {config_name}")
            except Exception as e:
                logger.error(f"Failed to load config {config_name}: {e}")

    def _reload_config(self, config_name: str) -> bool:
        """
        重新加载指定名称的配置

        Args:
            config_name: 配置名称

        Returns:
            bool: 是否成功重新加载
        """
        if config_name not in self._config_registry:
            logger.error(f"Unknown config name: {config_name}")
            return False

        try:
            config_class = self._config_registry[config_name]
            self._config_instances[config_name] = config_class.load()
            logger.info(f"{config_name.capitalize()} config reloaded")
            return True
        except Exception as e:
            logger.error(f"Failed to reload {config_name} config: {e}")
            return False

    def _validate_config_file(self, config_path: str) -> Tuple[bool, str]:
        """
        验证配置文件是否有效

        Args:
            config_path: 配置文件路径

        Returns:
            tuple: (is_valid, error_message) - 配置是否有效和错误信息
        """
        if config_path not in self._config_paths:
            return False, f"Unknown config path: {config_path}"

        config_name, config_class = self._config_paths[config_path]
        is_valid, error_message, _ = config_class.validate(config_path)
        return is_valid, error_message

    def _run_watcher(self) -> None:
        """在单独的线程中运行文件监控"""
        # 确保CONFIG_PATH目录存在
        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_PATH)

        # 根据环境选择最佳监控策略
        force_polling = True  # 在 Windows 上强制使用轮询可能更稳定

        while not self._should_stop:
            try:
                # 使用同步版本的 watch 函数
                for changes in watch(
                    CONFIG_PATH,
                    watch_filter=lambda change, path: str(path).endswith(".json"),
                    debounce=1000,  # 增加到1秒防抖动
                    step=500,  # 增加到500毫秒检查周期
                    yield_on_timeout=False,  # 不在超时时生成事件
                    force_polling=force_polling,  # 强制使用轮询，更稳定
                    poll_delay_ms=1000,  # 轮询延迟设为1秒
                    recursive=True,  # 递归监控子目录
                    rust_timeout=10000,  # 增加 rust_timeout 到10秒
                ):
                    if self._should_stop:
                        break

                    for change, path in changes:
                        norm_path = os.path.normpath(str(path))
                        path_basename = os.path.basename(norm_path)

                        # 查找匹配的配置路径
                        for config_path, (config_name, _) in self._config_paths.items():
                            norm_config_path = os.path.normpath(config_path)
                            config_basename = os.path.basename(norm_config_path)

                            # 检查文件名是否匹配
                            if path_basename == config_basename:
                                # 先验证配置文件是否有效
                                is_valid, error_message = self._validate_config_file(
                                    config_path
                                )

                                if not is_valid:
                                    logger.warning(
                                        f"检测到无效的配置文件: {os.path.basename(path)}, 错误: {error_message}"
                                    )
                                    continue  # 跳过无效的配置文件

                                # 重新加载配置
                                if self._reload_config(config_name):
                                    # ...余下的回调处理代码...
                                    # 重新加载配置
                                    if self._reload_config(config_name):
                                        # 成功重新加载配置后调用回调
                                        for callback in self._change_callbacks.get(
                                            config_path, set()
                                        ):
                                            try:
                                                # 处理异步回调
                                                if (
                                                    hasattr(callback, "__code__")
                                                    and callback.__code__.co_flags & 0x80
                                                ):
                                                    # 如果是异步函数，创建一个单独的线程来运行事件循环
                                                    threading.Thread(
                                                        target=self._run_async_callback,
                                                        args=(callback,),
                                                        daemon=True,
                                                    ).start()
                                                else:
                                                    # 同步函数直接调用
                                                    callback()
                                            except Exception as e:
                                                logger.error(f"配置变更回调执行出错: {e}")

            except KeyboardInterrupt:
                # 键盘中断优雅退出
                logger.info("配置监控接收到键盘中断信号")
                break
            except Exception as e:
                logger.error(f"文件监控遇到错误: {e}")
                # 如果监控失败，等待5秒后重试
                time.sleep(5)
                # 继续循环，不退出监控

        logger.info("配置文件监控已停止")

    def _run_async_callback(self, callback):
        """在单独的线程中运行异步回调"""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(callback())
        except Exception as e:
            logger.error(f"Error running async callback: {e}")
        finally:
            loop.close()

    def stop_watching(self):
        """停止文件监控"""
        self._should_stop = True
        if self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=2.0)
        logger.info("配置文件监控已停止")

    def register_change_callback(self, config_path: str, callback: Callable) -> None:
        """注册配置变更的回调函数"""
        if config_path in self._change_callbacks:
            self._change_callbacks[config_path].add(callback)
        else:
            logger.warning(f"尝试为未知配置路径注册回调: {config_path}")

    def unregister_change_callback(self, config_path: str, callback: Callable) -> None:
        """取消注册配置变更的回调函数"""
        if (
            config_path in self._change_callbacks
            and callback in self._change_callbacks[config_path]
        ):
            self._change_callbacks[config_path].remove(callback)

    def __getattr__(self, name: str) -> Any:
        """动态获取配置属性，支持 config_manager.mcim_config 这样的访问方式"""
        # 检查是否是 xxx_config 形式的属性
        if name.endswith("_config"):
            config_name = name[:-7]  # 去掉 _config 后缀
            if config_name in self._config_instances:
                return self._config_instances[config_name]

        # 如果不是配置属性，则抛出 AttributeError
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def reload_all(self) -> None:
        """强制重新加载所有配置"""
        for config_name in self._config_registry:
            self._reload_config(config_name)

    def get_config(self, config_name: str) -> Any:
        """按名称获取配置"""
        if config_name not in self._config_instances:
            raise ValueError(f"Unknown config name: {config_name}")
        return self._config_instances[config_name]


# 全局配置管理器单例
config_manager = ConfigManager()
