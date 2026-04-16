import json
import os
import platform
import time
import threading
import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


SETTING_FILE = 'setting.txt'

INFO_KEYS = ['os', 'os_version', 'cpu_type', 'cpu_cores', 'memory_size']
LOAD_KEYS = ['cpu_usage', 'memory_usage']


def load_settings():
    '''setting.txt 파일을 읽어 출력할 항목 목록을 반환한다.
    파일이 없으면 모든 항목을 기본값으로 반환한다.
    '''
    all_keys = INFO_KEYS + LOAD_KEYS
    try:
        with open(SETTING_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        valid = [line for line in lines if line in all_keys]
        if valid:
            return valid
        return all_keys
    except FileNotFoundError:
        return all_keys
    except PermissionError as e:
        print('setting.txt 읽기 권한이 없습니다:', e)
        return all_keys
    except OSError as e:
        print('setting.txt 처리 중 OS 오류:', e)
        return all_keys


class DummySensor:
    '''더미 센서 클래스 - LCG 알고리즘으로 화성 기지 환경 데이터 생성'''

    def __init__(self):
        '''DummySensor 초기화 - LCG 파라미터 및 env_values 설정'''
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0
        }
        self._lcg_state = id(object())
        self._lcg_a = 1664525
        self._lcg_c = 1013904223
        self._lcg_m = 2 ** 32
        now = datetime.datetime.now()
        self.log_filename = 'mars_mission_computer_{}.log'.format(
            now.strftime('%Y%m%d_%H%M%S')
        )

    def _next_lcg(self):
        '''LCG 알고리즘으로 다음 상태 계산 후 0~1 실수 반환'''
        self._lcg_state = (
            self._lcg_a * self._lcg_state + self._lcg_c
        ) % self._lcg_m
        return self._lcg_state / self._lcg_m

    def _rand_range(self, lo, hi):
        '''lo~hi 범위 랜덤 실수 생성 (소수점 2자리)'''
        return round(lo + self._next_lcg() * (hi - lo), 2)

    def set_env(self):
        '''LCG 랜덤값을 env_values 딕셔너리에 저장'''
        self.env_values['mars_base_internal_temperature'] = self._rand_range(18, 30)
        self.env_values['mars_base_external_temperature'] = self._rand_range(0, 21)
        self.env_values['mars_base_internal_humidity'] = self._rand_range(50, 60)
        self.env_values['mars_base_external_illuminance'] = self._rand_range(500, 715)
        self.env_values['mars_base_internal_co2'] = self._rand_range(0.02, 0.1)
        self.env_values['mars_base_internal_oxygen'] = self._rand_range(4, 7)

    def _get_now_str(self):
        '''현재 날짜시간 문자열 반환 (YYYY-MM-DD HH:MM:SS)'''
        now = datetime.datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')

    def get_env(self):
        '''env_values 반환 및 로그 파일에 CSV 한 줄 append 기록'''
        log_line = '{},{},{},{},{},{},{}\n'.format(
            self._get_now_str(),
            self.env_values['mars_base_internal_temperature'],
            self.env_values['mars_base_external_temperature'],
            self.env_values['mars_base_internal_humidity'],
            self.env_values['mars_base_external_illuminance'],
            self.env_values['mars_base_internal_co2'],
            self.env_values['mars_base_internal_oxygen']
        )
        try:
            with open(self.log_filename, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except FileNotFoundError as e:
            print('로그 파일을 찾을 수 없습니다:', e)
        except PermissionError as e:
            print('로그 파일 쓰기 권한이 없습니다:', e)
        except OSError as e:
            print('로그 파일 처리 중 OS 오류:', e)

        return self.env_values


class MissionComputer:
    '''미션 컴퓨터 클래스 - 센서 데이터 수집, 시스템 정보 및 부하 조회 기능 포함'''

    def __init__(self):
        '''MissionComputer 초기화 - env_values, DummySensor 인스턴스, 내부 상태 설정'''
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0
        }
        self.ds = DummySensor()
        self._running = False
        self._history = []
        self._last_avg_time = None

    def get_mission_computer_info(self):
        '''미션 컴퓨터의 시스템 정보를 수집하여 JSON 형식으로 출력한다.

        수집 항목:
            - os: 운영체계
            - os_version: 운영체계 버전
            - cpu_type: CPU 타입
            - cpu_cores: CPU 코어 수
            - memory_size: 메모리 크기 (GB)
        '''
        settings = load_settings()
        all_info = {}

        try:
            all_info['os'] = platform.system()
        except Exception as e:
            all_info['os'] = 'Unknown ({})'.format(e)

        try:
            all_info['os_version'] = platform.version()
        except Exception as e:
            all_info['os_version'] = 'Unknown ({})'.format(e)

        try:
            cpu_type = platform.processor()
            if not cpu_type:
                cpu_type = platform.machine()
            all_info['cpu_type'] = cpu_type
        except Exception as e:
            all_info['cpu_type'] = 'Unknown ({})'.format(e)

        try:
            all_info['cpu_cores'] = os.cpu_count()
        except Exception as e:
            all_info['cpu_cores'] = 'Unknown ({})'.format(e)

        try:
            if PSUTIL_AVAILABLE:
                mem_bytes = psutil.virtual_memory().total
                all_info['memory_size'] = '{:.2f} GB'.format(
                    mem_bytes / (1024 ** 3)
                )
            else:
                all_info['memory_size'] = 'psutil 미설치로 조회 불가'
        except Exception as e:
            all_info['memory_size'] = 'Unknown ({})'.format(e)

        result = {k: v for k, v in all_info.items() if k in settings}
        print(json.dumps(result, indent=4, ensure_ascii=False))

    def get_mission_computer_load(self):
        '''미션 컴퓨터의 실시간 부하 정보를 수집하여 JSON 형식으로 출력한다.

        수집 항목:
            - cpu_usage: CPU 실시간 사용량 (%)
            - memory_usage: 메모리 실시간 사용량 (%)
        '''
        settings = load_settings()
        all_load = {}

        try:
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=1)
                all_load['cpu_usage'] = '{:.1f}%'.format(cpu_percent)
            else:
                all_load['cpu_usage'] = 'psutil 미설치로 조회 불가'
        except Exception as e:
            all_load['cpu_usage'] = 'Unknown ({})'.format(e)

        try:
            if PSUTIL_AVAILABLE:
                mem_percent = psutil.virtual_memory().percent
                all_load['memory_usage'] = '{:.1f}%'.format(mem_percent)
            else:
                all_load['memory_usage'] = 'psutil 미설치로 조회 불가'
        except Exception as e:
            all_load['memory_usage'] = 'Unknown ({})'.format(e)

        result = {k: v for k, v in all_load.items() if k in settings}
        print(json.dumps(result, indent=4, ensure_ascii=False))

    def get_sensor_data(self):
        '''5초마다 센서 데이터를 읽어 env_values를 갱신하고 JSON으로 출력한다.
        엔터 키 입력 시 반복을 멈추고 System stoped....을 출력한다.
        5분마다 평균값을 별도로 출력한다.
        '''
        self._running = True
        self._last_avg_time = time.time()

        input_thread = threading.Thread(target=self._wait_for_stop, daemon=True)
        input_thread.start()

        while self._running:
            self.ds.set_env()
            sensor_data = self.ds.get_env()

            for key in self.env_values:
                self.env_values[key] = sensor_data[key]

            print(json.dumps(self.env_values, indent=4))

            self._history.append(dict(self.env_values))

            now = time.time()
            if now - self._last_avg_time >= 300:
                self._print_5min_avg()
                self._history = []
                self._last_avg_time = now

            for _ in range(50):
                if not self._running:
                    break
                time.sleep(0.1)

        print('System stoped....')

    def _wait_for_stop(self):
        '''엔터 키 입력 대기 후 실행 중단 플래그 설정'''
        input()
        self._running = False

    def _print_5min_avg(self):
        '''최근 5분간 수집된 환경 데이터의 평균값을 JSON 형식으로 출력한다.'''
        if not self._history:
            return
        avg = {}
        for key in self.env_values:
            vals = [h[key] for h in self._history]
            avg[key] = round(sum(vals) / len(vals), 2)
        print('=== 5분 평균 환경 데이터 ===')
        print(json.dumps(avg, indent=4))


runComputer = MissionComputer()
runComputer.get_mission_computer_info()
runComputer.get_mission_computer_load()
