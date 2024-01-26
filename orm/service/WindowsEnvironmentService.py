import winreg

from orm.model.WindowsEnvironment import WindowsEnvironment


class WindowsEnvironmentService:
    # 环境
    @staticmethod
    def get_system_env_var(environment_name):
        """
        查询环境变量
        """
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
        try:
            value, _ = winreg.QueryValueEx(key, environment_name)
            return value
        except FileNotFoundError:
            return None
        finally:
            winreg.CloseKey(key)

    @staticmethod
    def set_system_env_var(environment_name, environment_value):
        """
        增加/修改环境变量
        """
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, environment_name, 0, winreg.REG_SZ, environment_value)
        winreg.CloseKey(key)

    @staticmethod
    def delete_system_env_var(environment_name):
        """
        删除环境变量
        """
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, environment_name)
        winreg.CloseKey(key)

    # Path
    @staticmethod
    def delete_path(environment_name, path_value):
        sys_environment_value = WindowsEnvironmentService.get_system_env_var(environment_name)
        if sys_environment_value is None:
            return

        sys_path_value = WindowsEnvironmentService.get_path()
        sys_path_value = sys_path_value.replace(path_value, "")

        WindowsEnvironmentService.set_system_env_var("path", sys_path_value)

    @staticmethod
    def get_path():
        return WindowsEnvironmentService.get_system_env_var("PATH")

    @staticmethod
    def set_path():
        """
        设置path
        """
        # path的必须是以;结尾
        sys_path_value = WindowsEnvironmentService.get_path()
        if not sys_path_value.endswith(";"):
            sys_path_value += ";"

        sys_path_value += WindowsEnvironment.path_value

        # /M 参数用于修改系统级环境变量
        WindowsEnvironmentService.set_system_env_var("path", sys_path_value)

    @staticmethod
    def broadcast_environment_change():

        # 方式1：重启explorer.exe，有时管用
        try:
            # 使用cmd执行命令 taskkill /f /im explorer.exe && explorer.exe
            import subprocess
            # print("设置环境变量...")
            # # 杀死explorer进程
            # subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'])
            # # 重启explorer进程
            # subprocess.run('explorer.exe')

            # 使用cmd执行命令 setx /M path "%path%"
            print("设置环境变量...")
            subprocess.run(['setx', '/M', 'path', WindowsEnvironmentService.get_path()])
            print("设置环境变量成功")
        except Exception as e:
            print(f"Error occurred: {e}")
