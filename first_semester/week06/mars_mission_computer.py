import json
import time
import threading
import datetime


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
    '''미션 컴퓨터 클래스 - 센서 데이터를 수집하고 JSON 형식으로 출력'''

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


RunComputer = MissionComputer()
RunComputer.get_sensor_data()
