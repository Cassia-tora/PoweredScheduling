import pymysql
import logging
from datetime import datetime

# 配置日志记录
logging.basicConfig(
    filename='db_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 数据库连接类
class DBConnection:
    def __init__(self):
        self.host = 'rm-wz9y6p1jk07522xb0ho.mysql.rds.aliyuncs.com'
        self.user = 'user_jueming'
        self.password = '7za&V!LrMcMhpf'
        self.database = 'xwerp-jianguo'
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            error_msg = f"数据库连接错误: {str(e)}"
            print(error_msg)
            logging.error(error_msg)  # 记录连接错误到日志
            return False

    def close(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                error_msg = f"数据库关闭错误: {str(e)}"
                print(error_msg)
                logging.error(error_msg)  # 记录关闭错误到日志
            finally:
                self.connection = None

    def execute_insert(self, query, params=None):
        """执行INSERT语句并返回最后插入的ID"""
        if not self.connection:
            if not self.connect():
                return None
        try:
            with self.connection.cursor() as cursor:
                # 执行插入语句
                cursor.execute(query, params or ())
                # 提交事务
                self.connection.commit()
                # 返回最后插入记录的ID
                return cursor.lastrowid
        except Exception as e:
            # 发生错误时回滚事务
            self.connection.rollback()
            # 格式化错误信息，保持与execute_query一致的格式
            error_msg = f"插入错误 [SQL: {query}] [参数: {params}]: {str(e)}"
            print(error_msg)
            logging.error(error_msg)  # 记录插入错误到日志
            return None

    def execute_query(self, query, params=None):
        if not self.connection:
            if not self.connect():
                return None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchall()
                return result
        except Exception as e:
            error_msg = f"查询错误 [SQL: {query}] [参数: {params}]: {str(e)}"
            print(error_msg)
            logging.error(error_msg)  # 记录查询错误到日志
            return None

    def execute_update(self, query, params=None):
        if not self.connection:
            if not self.connect():
                return False
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                self.connection.commit()
                return True
        except Exception as e:
            error_msg = f"更新错误 [SQL: {query}] [参数: {params}]: {str(e)}"
            print(error_msg)
            logging.error(error_msg)  # 记录更新错误到日志
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception as rollback_err:
                    rollback_msg = f"事务回滚错误: {str(rollback_err)}"
                    print(rollback_msg)
                    logging.error(rollback_msg)
            return False
        
    def begin_transaction(self):
        """开始事务（关闭自动提交）"""
        if self.connection:
            self.connection.autocommit(False)

    def commit(self):
        """提交事务"""
        if self.connection:
            try:
                self.connection.commit()
            except Exception as e:
                error_msg = f"事务提交错误: {str(e)}"
                print(error_msg)
                logging.error(error_msg)
                return False
            return True
        return False

    def rollback(self):
        """回滚事务"""
        if self.connection:
            try:
                self.connection.rollback()
            except Exception as e:
                error_msg = f"事务回滚错误: {str(e)}"
                print(error_msg)
                logging.error(error_msg)
                return False
            return True
        return False
