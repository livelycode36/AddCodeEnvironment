from peewee import *

db = SqliteDatabase('config.db')


class WindowsEnvironment(Model):
    id = AutoField()  # 主键字段
    key = CharField()
    value = CharField()
    add_path = CharField()

    class Meta:
        database = db
        table_name = 'windows_environment'

    @property
    def path_value(self):
        if self.key == "JAVA_HOME":
            return fr"%{self.key}%{self.add_path}%{self.key}%\jre\bin;"  # %JAVA_HOME%\bin;%JAVA_HOME%\jre\bin;

        return fr"%{self.key}%{self.add_path}"


def initialize_data():
    # 如果表的的数据是空的，则插入初始化数据
    if WindowsEnvironment.select().count() == 0:
        initial_data = [
            {"key": "JAVA_HOME", "value": r"D:\DevelopmentTools\Softare\GreenSoftWare\a-language\jdk\Java1.8",
             "add_path": r"\bin;"},
            {"key": "MAVEN_HOME",
             "value": r"D:\DevelopmentTools\Softare\GreenSoftWare\a-language\Maven\apache-maven-3.9.1",
             "add_path": r"\bin;"},
            {"key": "GROOVY_HOME",
             "value": r"D:\DevelopmentTools\Softare\GreenSoftWare\a-language\groovy\groovy-4.0.13",
             "add_path": r"\bin;"},
            {"key": "GRADLE_HOME", "value": r"D:\DevelopmentTools\Softare\GreenSoftWare\a-language\Gradle\gradle",
             "add_path": r"\bin;"},
            {"key": "GRADLE_USER_HOME", "value": r"D:\DevelopmentTools\Softare\repository\gradle-repository",
             "add_path": r"\bin;"},
            {"key": "NODE_HOME",
             "value": r"D:\DevelopmentTools\Softare\GreenSoftWare\a-language\NodeJS\node-v17.8.0-win-x64",
             "add_path": r";"},
            {"key": "NODE_GLOBAL",
             "value": r"D:\DevelopmentTools\Softare\GreenSoftWare\a-language\NodeJS\data\node_global",
             "add_path": r";"}
        ]

        for data in initial_data:
            WindowsEnvironment.create(**data)


db.connect()
db.create_tables([WindowsEnvironment])
initialize_data()

db.close()
