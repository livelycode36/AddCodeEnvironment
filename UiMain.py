import os
import sys

from PyQt6 import QtWidgets, uic

from XmlService import XmlService
from orm.model.WindowsEnvironment import WindowsEnvironment
from orm.service.WindowsEnvironmentService import WindowsEnvironmentService


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('ui.ui', self)

        self.init_table()

        self.findChild(QtWidgets.QPushButton, 'add_environment').clicked.connect(self.add_environment_callback)
        self.findChild(QtWidgets.QPushButton, 'delete_environment').clicked.connect(self.delete_environment_callback)

        self.init_maven_config()
        self.init_node_config()

    def init_table(self):
        # 假设你的.ui文件中有一个ObjectName为"key_value_path"的按钮
        self.table_key_value_path: QtWidgets.QTableWidget = self.findChild(QtWidgets.QTableWidget, 'key_value_path')
        # 为按钮绑定事件处理函数
        self.findChild(QtWidgets.QPushButton, 'add_row').clicked.connect(self.add_row_callback)
        self.findChild(QtWidgets.QPushButton, 'delete_select_row').clicked.connect(self.delete_select_rows_callback)

        self.load_table_data()

        # 为表格的单元格内容改变事件绑定事件处理函数
        # PyQt 表格中内容发生变化时，同步更新 SQLite3 数据库中的数据，你需要连接表格的编辑信号到一个槽函数，然后在这个槽函数中执行数据库的更新操作。
        # 在 PyQt 的 QTableWidget 中，可以使用 itemChanged 信号来监听单元格内容的更改。
        self.table_key_value_path.itemChanged.connect(self.on_item_changed)

    def load_table_data(self):
        assert type(self.table_key_value_path) is QtWidgets.QTableWidget, "获取表格错误"
        # 清除表格现有数据
        self.table_key_value_path.setRowCount(0)
        self.table_key_value_path.clearContents()

        # 设置表格的列数和行数
        self.table_key_value_path.setColumnCount(4)  # 设置列数
        self.table_key_value_path.setHorizontalHeaderLabels(['id', 'key', 'value', 'add_path'])
        self.table_key_value_path.setRowCount(WindowsEnvironment.select().count())  # 设置行数
        # 从数据库加载数据
        query = WindowsEnvironment.select()
        index = 0
        for record in query:
            self.table_key_value_path.setItem(index, 0, QtWidgets.QTableWidgetItem(str(record.id)))
            self.table_key_value_path.setItem(index, 1, QtWidgets.QTableWidgetItem(record.key))
            self.table_key_value_path.setItem(index, 2, QtWidgets.QTableWidgetItem(record.value))
            self.table_key_value_path.setItem(index, 3, QtWidgets.QTableWidgetItem(record.add_path))
            index += 1

        self.adjust_table_size()

    def adjust_table_size(self):
        """
        根据表格内容，调整表格大小
        :return:
        """
        for i in range(self.table_key_value_path.columnCount()):
            self.table_key_value_path.resizeColumnToContents(i)
        for i in range(self.table_key_value_path.rowCount()):
            self.table_key_value_path.resizeRowToContents(i)

    def add_row_callback(self):
        # 在数据库中添加新行
        WindowsEnvironment.create(key="", value="", add_path="")
        # 更新表格
        self.load_table_data()

    def delete_select_rows_callback(self):
        selected_items = self.table_key_value_path.selectedItems()
        if not selected_items:
            return

        selected_rows = {item.row() for item in selected_items}
        for row in selected_rows:
            # 获取 ID 并删除数据库记录
            id_item = self.table_key_value_path.item(row, 0)
            if id_item is not None:
                record_id = int(id_item.text())
                WindowsEnvironment.delete().where(WindowsEnvironment.id == record_id).execute()

        # 更新表格
        self.load_table_data()

    def on_item_changed(self, item):
        row = item.row()
        column = item.column()
        new_value = item.text()

        # 获取该行对应的数据库记录的 ID
        id_item = self.table_key_value_path.item(row, 0)
        if id_item is None:
            return
        record_id = int(id_item.text())

        # 更新数据库
        self.update_database(record_id, column, new_value)

    def update_database(self, record_id, column, new_value):
        # 使用 Peewee 更新数据库
        field_map = {1: WindowsEnvironment.key, 2: WindowsEnvironment.value,
                     3: WindowsEnvironment.add_path}
        field = field_map.get(column)
        if field is not None:
            query = WindowsEnvironment.update({field: new_value}).where(
                WindowsEnvironment.id == record_id)
            query.execute()

    def add_environment_callback(self):
        # 从数据库加载数据
        windows_environments = WindowsEnvironment.select()

        # 设置系统环境变量
        for windows_environment in windows_environments:
            WindowsEnvironmentService.set_system_env_var(windows_environment.key, windows_environment.value)

        sys_path = WindowsEnvironmentService.get_path()
        for windows_environment in windows_environments:
            if sys_path.find(windows_environment.path_value) == -1:
                sys_path = sys_path + windows_environment.path_value

        WindowsEnvironmentService.set_system_env_var("PATH", sys_path)
        # 通知系统环境变量已经改变
        WindowsEnvironmentService.broadcast_environment_change()

    def delete_environment_callback(self):
        # 从数据库加载数据
        windows_environments = WindowsEnvironment.select()

        # 删除系统环境变量
        for windows_environment in windows_environments:
            WindowsEnvironmentService.delete_system_env_var(windows_environment.key)

        sys_path = WindowsEnvironmentService.get_path()
        for windows_environment in windows_environments:
            if sys_path.find(windows_environment.path_value) != -1:
                sys_path = sys_path.replace(windows_environment.path_value, "")

        WindowsEnvironmentService.set_system_env_var("PATH", sys_path)
        # 通知系统环境变量已经改变
        WindowsEnvironmentService.broadcast_environment_change()

    def on_local_repository_changed(self):
        result = self.local_repository.text()
        # 修改
        self.xml_service.data["settings"]["localRepository"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_proxy_enable_changed(self):
        # 获取当前状态
        result = self.proxy_enable.isChecked()
        print(f"当前状态{result}")
        if result:
            # 修改
            self.xml_service.data["settings"]["proxies"] = {
                'proxy': {
                    'id': 'optional',
                    'active': 'true',
                    'protocol': 'http',
                    'host': '127.0.0.1',
                    'port': '10809'
                }
            }
            # 保存
            self.xml_service.write_xml(self.xml_service.data)

            self.xml_service.read_xml()
            # proxy_id
            self.proxy_id = self.findChild(QtWidgets.QLineEdit, 'proxy_id')
            self.proxy_id.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["id"])
            self.proxy_id.textChanged.connect(self.on_proxy_id_changed)
            # proxy_active
            self.proxy_active = self.findChild(QtWidgets.QLineEdit, 'proxy_active')
            self.proxy_active.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["active"])
            self.proxy_active.textChanged.connect(self.on_proxy_active_changed)
            # proxy_protocol
            self.proxy_protocol = self.findChild(QtWidgets.QLineEdit, 'proxy_protocol')
            self.proxy_protocol.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["protocol"])
            self.proxy_protocol.textChanged.connect(self.on_proxy_protocol_changed)
            # proxy_host
            self.proxy_host = self.findChild(QtWidgets.QLineEdit, 'proxy_host')
            self.proxy_host.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["host"])
            self.proxy_host.textChanged.connect(self.on_proxy_host_changed)
            # proxy_port
            self.proxy_port = self.findChild(QtWidgets.QLineEdit, 'proxy_port')
            self.proxy_port.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["port"])
            self.proxy_port.textChanged.connect(self.on_proxy_port_changed)

        if result is False:
            # 修改
            self.xml_service.data["settings"]["proxies"] = None
            # 保存
            self.xml_service.write_xml(self.xml_service.data)

    def on_proxy_id_changed(self):
        result = self.proxy_id.text()
        # 修改
        self.xml_service.data["settings"]["proxies"]["proxy"]["id"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_proxy_active_changed(self):
        result = self.proxy_active.isChecked()
        # 修改
        self.xml_service.data["settings"]["proxies"]["active"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_proxy_protocol_changed(self):
        result = self.proxy_protocol.currentText()
        # 修改
        self.xml_service.data["settings"]["proxies"]["proxy"]["protocol"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_proxy_host_changed(self):
        result = self.proxy_host.text()
        # 修改
        self.xml_service.data["settings"]["proxies"]["proxy"]["host"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_proxy_port_changed(self):
        result = self.proxy_port.text()
        # 修改
        self.xml_service.data["settings"]["proxies"]["proxy"]["port"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_mirror_id_changed(self):
        result = self.mirror_id.text()
        # 修改
        self.xml_service.data["settings"]["mirrors"]["mirror"]["id"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_mirror_name_changed(self):
        result = self.mirror_name.text()
        # 修改
        self.xml_service.data["settings"]["mirrors"]["mirror"]["name"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_mirror_url_changed(self):
        result = self.mirror_url.text()
        # 修改
        self.xml_service.data["settings"]["mirrors"]["mirror"]["url"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def on_mirror_mirrorOf_changed(self):
        result = self.mirror_mirrorOf.text()
        # 修改
        self.xml_service.data["settings"]["mirrors"]["mirror"]["mirrorOf"] = result
        # 保存
        self.xml_service.write_xml(self.xml_service.data)

    def init_maven_config(self):
        # M2_HOME
        try:
            filename = WindowsEnvironmentService.get_system_env_var("M2_HOME") + r"\conf\settings.xml"
        except TypeError:
            self.findChild(QtWidgets.QLineEdit, 'local_repository').setText(
                r"目前用户没有设置M2_HOME环境变量!!此处设置全部不生效")
            return
        # 如果判断文件，不存在则返回
        if not os.path.exists(filename):
            return
        # 将源文件，备份为settings.xml.bak
        if not os.path.exists(filename + ".bak"):
            import shutil
            shutil.copyfile(filename, filename + ".bak")

        self.xml_service = XmlService(filename)
        self.xml_service.read_xml()

        # local_repository
        self.local_repository = self.findChild(QtWidgets.QLineEdit, 'local_repository')
        # 回显
        try:
            if self.xml_service.data["settings"]["localRepository"] is not None:
                self.local_repository.setText(self.xml_service.data["settings"]["localRepository"])
        except KeyError:
            # 赋予默认值
            self.local_repository.setText(r"目前用户没有设置本地仓库的位置，将使用maven的默认值")
            self.on_local_repository_changed
        # 绑定事件
        self.local_repository.textChanged.connect(self.on_local_repository_changed)

        self.proxy_enable = self.findChild(QtWidgets.QCheckBox, 'proxy_checkbox')
        assert type(self.proxy_enable) is QtWidgets.QCheckBox, f"获取复选框错误：{type(self.proxy_enable)}"
        # 配置文件中存在，代理数据，则打勾✔
        try:
            if self.xml_service.data["settings"]["proxies"]["proxy"] is not None:
                self.proxy_enable.setChecked(True)
            else:
                self.proxy_enable.setChecked(False)
        except Exception:
            self.proxy_enable.setChecked(False)
        # 设置回调
        self.proxy_enable.stateChanged.connect(self.on_proxy_enable_changed)

        if self.proxy_enable.isChecked():
            # proxy_id
            self.proxy_id = self.findChild(QtWidgets.QLineEdit, 'proxy_id')
            self.proxy_id.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["id"])
            self.proxy_id.textChanged.connect(self.on_proxy_id_changed)
            # proxy_active
            self.proxy_active = self.findChild(QtWidgets.QLineEdit, 'proxy_active')
            self.proxy_active.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["active"])
            self.proxy_active.textChanged.connect(self.on_proxy_active_changed)
            # proxy_protocol
            self.proxy_protocol = self.findChild(QtWidgets.QLineEdit, 'proxy_protocol')
            self.proxy_protocol.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["protocol"])
            self.proxy_protocol.textChanged.connect(self.on_proxy_protocol_changed)
            # proxy_host
            self.proxy_host = self.findChild(QtWidgets.QLineEdit, 'proxy_host')
            self.proxy_host.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["host"])
            self.proxy_host.textChanged.connect(self.on_proxy_host_changed)
            # proxy_port
            self.proxy_port = self.findChild(QtWidgets.QLineEdit, 'proxy_port')
            self.proxy_port.setText(self.xml_service.data["settings"]["proxies"]["proxy"]["port"])
            self.proxy_port.textChanged.connect(self.on_proxy_port_changed)

        # mirror_id
        self.mirror_id = self.findChild(QtWidgets.QLineEdit, 'mirror_id')
        self.mirror_id.setText(self.xml_service.data["settings"]["mirrors"]["mirror"]["id"])
        self.mirror_id.textChanged.connect(self.on_mirror_id_changed)
        # mirror_name
        self.mirror_name = self.findChild(QtWidgets.QLineEdit, 'mirror_name')
        self.mirror_name.setText(self.xml_service.data["settings"]["mirrors"]["mirror"]["name"])
        self.mirror_name.textChanged.connect(self.on_mirror_name_changed)
        # mirror_url
        self.mirror_url = self.findChild(QtWidgets.QLineEdit, 'mirror_url')
        self.mirror_url.setText(self.xml_service.data["settings"]["mirrors"]["mirror"]["url"])
        self.mirror_url.textChanged.connect(self.on_mirror_url_changed)
        # mirror_mirrorOf
        self.mirror_mirrorOf = self.findChild(QtWidgets.QLineEdit, 'mirror_mirrorOf')
        self.mirror_mirrorOf.setText(self.xml_service.data["settings"]["mirrors"]["mirror"]["mirrorOf"])
        self.mirror_mirrorOf.textChanged.connect(self.on_mirror_mirrorOf_changed)

    def on_npmrc_changed(self):
        result = self.npmrc.toPlainText()
        # 修改
        filename = WindowsEnvironmentService.get_system_env_var("NODE_HOME") + r"\etc\npmrc"
        with open(filename, 'w') as f:
            f.write(result)

    def init_node_config(self):
        # NODE_HOME
        self.npmrc = self.findChild(QtWidgets.QPlainTextEdit, 'npmrc_config')
        print(type(self.npmrc))
        try:
            filename = WindowsEnvironmentService.get_system_env_var("NODE_HOME") + r"\etc\npmrc"
        except TypeError:
            self.npmrc.setPlainText(r"目前用户没有设置NODE_HOME环境变量!!此处设置全部不生效")
            return

        # 如果判断文件，不存在则新建文件，并初始化内容
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(r'prefix="D:/DevelopmentTools/Softare/GreenSoftWare/a-language/NodeJS/data/node_global"')
                f.write(r'cache="D:/DevelopmentTools/Softare/GreenSoftWare/a-language/NodeJS/data/node_cache"')
                f.write(r'registry="https://registry.npmmirror.com/"')

        # 将源文件，备份为settings.xml.bak
        if not os.path.exists(filename + ".bak"):
            import shutil
            shutil.copyfile(filename, filename + ".bak")

        # 回显
        with open(filename, 'r') as f:
            self.npmrc.setPlainText(f.read())
        # 绑定事件
        self.npmrc.textChanged.connect(self.on_npmrc_changed)


def admin_running():
    import ctypes
    import sys
    import os

    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    if not is_admin:
        print([sys.argv[0]])
        # 以管理员身份运行脚本
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                            " ".join([os.path.abspath(sys.argv[0])] + sys.argv[1:]), None, 1)
        # 退出，非管理员运行的脚本
        exit(0)


# admin_running()
app = QtWidgets.QApplication(sys.argv)
window = MyWindow()

window.show()
sys.exit(app.exec())
