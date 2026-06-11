"""화성 날씨 데이터(mars_weathers_data.csv)를 MySQL 테이블에 입력하는 모듈."""

import csv
import os

import pymysql


CSV_FILE = 'mars_weathers_data.csv'

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'mars1234',
    'database': 'mars_db',
    'charset': 'utf8mb4',
}

CREATE_TABLE_SQL = (
    'CREATE TABLE IF NOT EXISTS mars_weather ('
    '    weather_id INT NOT NULL AUTO_INCREMENT,'
    '    mars_date DATETIME NOT NULL,'
    '    temp FLOAT,'
    '    storm INT,'
    '    PRIMARY KEY (weather_id)'
    ')'
)

INSERT_SQL = (
    'INSERT INTO mars_weather (mars_date, temp, storm) VALUES (%s, %s, %s)'
)


class MySQLHelper:
    """MySQL 연결과 쿼리 실행을 간편하게 다루기 위한 도우미 클래스."""

    def __init__(self, config):
        """접속 설정을 받아 보관한다."""
        self.config = config
        self.connection = None

    def connect(self):
        """데이터베이스에 연결한다."""
        self.connection = pymysql.connect(**self.config)

    def execute(self, query, params=None):
        """단일 쿼리를 실행하고 변경 사항을 커밋한다."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
        self.connection.commit()

    def execute_many(self, query, seq_of_params):
        """여러 행을 한 번에 실행하고 커밋한 뒤 처리된 행 수를 반환한다."""
        with self.connection.cursor() as cursor:
            affected = cursor.executemany(query, seq_of_params)
        self.connection.commit()
        return affected

    def fetch_all(self, query, params=None):
        """조회 쿼리를 실행해 전체 결과를 반환한다."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def close(self):
        """연결을 종료한다."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None


def read_weather_csv(file_path):
    """CSV 파일을 읽어 (mars_date, temp, storm) 튜플 목록으로 반환한다.

    제공된 CSV의 폭풍 컬럼 헤더는 'stom'으로 되어 있으므로 해당 키를 사용한다.
    """
    rows = []
    with open(file_path, 'r', encoding='utf-8', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append((
                row['mars_date'],
                float(row['temp']),
                int(row['stom']),
            ))
    return rows


def main():
    """CSV 내용을 확인하고 mars_weather 테이블에 입력한다."""
    if not os.path.exists(CSV_FILE):
        print('CSV 파일을 찾을 수 없습니다: ' + CSV_FILE)
        return

    try:
        weather_rows = read_weather_csv(CSV_FILE)
    except (OSError, ValueError, KeyError) as error:
        print('CSV 읽기 중 오류가 발생했습니다: ' + str(error))
        return

    print('읽어 들인 행 수: ' + str(len(weather_rows)))
    for row in weather_rows:
        print(row)

    helper = MySQLHelper(DB_CONFIG)
    try:
        helper.connect()
        helper.execute(CREATE_TABLE_SQL)
        inserted = helper.execute_many(INSERT_SQL, weather_rows)
        print('테이블에 입력된 행 수: ' + str(inserted))

        total = helper.fetch_all('SELECT COUNT(*) FROM mars_weather')
        print('현재 mars_weather 전체 행 수: ' + str(total[0][0]))
    except pymysql.MySQLError as error:
        print('데이터베이스 처리 중 오류가 발생했습니다: ' + str(error))
    finally:
        helper.close()


if __name__ == '__main__':
    main()
