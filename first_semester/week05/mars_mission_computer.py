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
            with open('mars_mission_computer.log', 'a', encoding='utf-8') as f:
                f.write(log_line)
        except FileNotFoundError as e:
            print('로그 파일을 찾을 수 없습니다:', e)
        except PermissionError as e:
            print('로그 파일 쓰기 권한이 없습니다:', e)
        except OSError as e:
            print('로그 파일 처리 중 OS 오류:', e)

        return self.env_values


if __name__ == '__main__':
    ds = DummySensor()
    ds.set_env()
    print(ds.get_env())
