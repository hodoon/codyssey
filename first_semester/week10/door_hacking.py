'''
door_hacking.py - 비상 보관함 잠금 해제 도구

탐색 전략 비교:
  1. 브루트포스 (unlock_zip):
     단일 프로세스 순차 탐색, 최악의 경우 O(36^6) 약 21억 회 시도
  2. 순서 최적화 (unlock_zip with generate_ordered_candidates):
     확률 높은 패턴을 먼저 탐색하여 평균 탐색 범위를 대폭 축소
  3. 멀티프로세싱 + 순서 최적화 (unlock_zip_fast):
     후보 리스트를 CPU 코어 수로 균등 분할하여 병렬 처리, 속도 배수 향상
'''
import zipfile
import itertools
import time
import string
import multiprocessing


ZIP_FILE = 'emergency_storage_key.zip'
PASSWORD_FILE = 'password.txt'
CHARS = string.digits + string.ascii_lowercase
PASSWORD_LENGTH = 6
PRINT_INTERVAL = 100000

PHASE_LABELS = {
    1: '혼합패턴 탐색 중',
    2: '블록패턴 탐색 중',
    3: '알파벳 시작 탐색 중',
    4: '숫자 시작 탐색 중',
    5: '나머지 전체 탐색 중',
}


def generate_ordered_candidates():
    '''확률 높은 패턴부터 순서대로 패스워드 후보를 생성하는 제너레이터.

    각 항목은 (phase, password_str, password_bytes) 튜플로 yield한다.
    password_bytes는 zf.read() 호출 시 바로 사용할 수 있도록 미리 인코딩한 값이다.

    Phase 1: 숫자+알파벳 교대 혼합 패턴 (예: a1b2c3, 1a2b3c)
    Phase 2: 알파벳 앞 3자리 + 숫자 뒤 3자리, 또는 그 반대 (예: abc123, 123abc)
    Phase 3: 첫 글자가 알파벳인 모든 조합 (Phase 1,2 중복 허용)
    Phase 4: 첫 글자가 숫자인 모든 조합 (Phase 1,2 중복 허용)
    Phase 5: 나머지 전체 조합 (Phase 3,4 중복 허용)
    '''
    digits_chars = string.digits
    alpha_chars = string.ascii_lowercase

    # Phase 1: 교대 혼합 패턴 (L-D-L-D-L-D)
    for combo in itertools.product(
        alpha_chars, digits_chars, alpha_chars,
        digits_chars, alpha_chars, digits_chars
    ):
        pwd = ''.join(combo)
        yield 1, pwd, pwd.encode('utf-8')

    # Phase 1: 교대 혼합 패턴 (D-L-D-L-D-L)
    for combo in itertools.product(
        digits_chars, alpha_chars, digits_chars,
        alpha_chars, digits_chars, alpha_chars
    ):
        pwd = ''.join(combo)
        yield 1, pwd, pwd.encode('utf-8')

    # Phase 2: 알파벳 앞 3자리 + 숫자 뒤 3자리 (AAA-DDD)
    for combo in itertools.product(
        alpha_chars, alpha_chars, alpha_chars,
        digits_chars, digits_chars, digits_chars
    ):
        pwd = ''.join(combo)
        yield 2, pwd, pwd.encode('utf-8')

    # Phase 2: 숫자 앞 3자리 + 알파벳 뒤 3자리 (DDD-AAA)
    for combo in itertools.product(
        digits_chars, digits_chars, digits_chars,
        alpha_chars, alpha_chars, alpha_chars
    ):
        pwd = ''.join(combo)
        yield 2, pwd, pwd.encode('utf-8')

    # Phase 3: 첫 글자가 알파벳인 모든 조합
    for combo in itertools.product(alpha_chars, CHARS, CHARS, CHARS, CHARS, CHARS):
        pwd = ''.join(combo)
        yield 3, pwd, pwd.encode('utf-8')

    # Phase 4: 첫 글자가 숫자인 모든 조합
    for combo in itertools.product(digits_chars, CHARS, CHARS, CHARS, CHARS, CHARS):
        pwd = ''.join(combo)
        yield 4, pwd, pwd.encode('utf-8')

    # Phase 5: 나머지 전체 조합
    for combo in itertools.product(CHARS, repeat=PASSWORD_LENGTH):
        pwd = ''.join(combo)
        yield 5, pwd, pwd.encode('utf-8')


def save_password(password):
    '''해독한 암호를 password.txt 파일에 저장한다.'''
    try:
        with open(PASSWORD_FILE, 'w', encoding='utf-8') as f:
            f.write(password)
        print('암호가 {}에 저장되었습니다.'.format(PASSWORD_FILE))
    except FileNotFoundError as e:
        print('파일을 찾을 수 없습니다:', e)
    except PermissionError as e:
        print('파일 쓰기 권한이 없습니다:', e)
    except OSError as e:
        print('파일 처리 중 OS 오류:', e)


def _search_chunk(args):
    '''담당 구간의 패스워드 후보를 순차 탐색한다.

    반환값:
        ('success', phase, password): 암호 발견
        ('error', message): 파일 접근 오류
        None: 암호 미발견 또는 stop_flag로 중단
    '''
    zip_path, chunk, stop_flag = args
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            name = zf.namelist()[0]
            for phase, password, pwd_bytes in chunk:
                if stop_flag.value == 1:
                    return None
                try:
                    zf.read(name, pwd=pwd_bytes)
                    stop_flag.value = 1
                    return 'success', phase, password
                except Exception:
                    pass
    except FileNotFoundError as e:
        return 'error', 'ZIP 파일을 찾을 수 없습니다: {}'.format(e)
    except PermissionError as e:
        return 'error', 'ZIP 파일 읽기 권한이 없습니다: {}'.format(e)
    except OSError as e:
        return 'error', 'ZIP 파일 처리 중 OS 오류: {}'.format(e)
    return None


def unlock_zip(zip_path):
    '''generate_ordered_candidates()로 우선순위 패턴부터 탐색하여 ZIP 파일의 암호를 해독한다.'''
    start_time = time.time()
    start_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print('[시작] {}'.format(start_str))

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            name = zf.namelist()[0]
            count = 0
            for phase, password, pwd_bytes in generate_ordered_candidates():
                count += 1

                if count % PRINT_INTERVAL == 0:
                    elapsed = time.time() - start_time
                    label = PHASE_LABELS.get(phase, '탐색 중')
                    print('[Phase {} - {}] 시도 #{} | 경과 시간: {:.2f}초'.format(
                        phase, label, count, elapsed
                    ))

                try:
                    zf.read(name, pwd=pwd_bytes)
                    elapsed = time.time() - start_time
                    print('[성공] 암호: {} | Phase {}에서 발견 | 총 소요 시간: {:.2f}초'.format(
                        password, phase, elapsed
                    ))
                    save_password(password)
                    return password
                except Exception:
                    pass

    except FileNotFoundError as e:
        print('ZIP 파일을 찾을 수 없습니다:', e)
    except PermissionError as e:
        print('ZIP 파일 읽기 권한이 없습니다:', e)
    except OSError as e:
        print('ZIP 파일 처리 중 OS 오류:', e)

    elapsed = time.time() - start_time
    print('[실패] 암호를 찾지 못했습니다. | 총 소요 시간: {:.2f}초'.format(elapsed))
    return None


def unlock_zip_fast(zip_path):
    '''멀티프로세싱으로 병렬 탐색하여 ZIP 파일의 암호를 해독한다.

    generate_ordered_candidates()의 후보를 BATCH_SIZE 단위로 수집하고
    CPU 코어 수로 균등 분할하여 병렬 처리한다.
    성공한 프로세스가 Manager 공유 변수를 통해 나머지 프로세스를 즉시 종료한다.
    '''
    start_time = time.time()
    start_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print('[시작] {}'.format(start_str))

    num_cores = multiprocessing.cpu_count()
    print('CPU 코어 수: {}'.format(num_cores))

    batch_size = num_cores * 50000  # 코어당 5만 개 기준

    manager = multiprocessing.Manager()
    stop_flag = manager.Value('i', 0)

    found_password = None
    found_phase = None
    total_count = 0

    pool = multiprocessing.Pool(processes=num_cores)
    try:
        gen = generate_ordered_candidates()

        while stop_flag.value == 0:
            # generate_ordered_candidates() 후보를 batch_size 단위로 수집 후 균등 분할
            batch = []
            for item in gen:
                batch.append(item)
                if len(batch) >= batch_size:
                    break

            if not batch:
                break

            chunk_size = max(1, (len(batch) + num_cores - 1) // num_cores)
            chunks = [
                batch[i:i + chunk_size]
                for i in range(0, len(batch), chunk_size)
            ]

            args_list = [(zip_path, chunk, stop_flag) for chunk in chunks]

            for result in pool.imap_unordered(_search_chunk, args_list):
                if result is None:
                    continue
                status = result[0]
                if status == 'success':
                    _, found_phase, found_password = result
                    pool.terminate()
                    break
                if status == 'error':
                    print(result[1])

            total_count += len(batch)

            if found_password:
                break

            elapsed = time.time() - start_time
            last_phase = batch[-1][0]
            label = PHASE_LABELS.get(last_phase, '탐색 중')
            print('[Phase {} - {}] 시도 #{} | 경과 시간: {:.2f}초'.format(
                last_phase, label, total_count, elapsed
            ))

    finally:
        pool.terminate()
        pool.join()

    elapsed = time.time() - start_time
    if found_password:
        print('[성공] 암호: {} | Phase {}에서 발견 | 총 소요 시간: {:.2f}초'.format(
            found_password, found_phase, elapsed
        ))
        save_password(found_password)
    else:
        print('[실패] 암호를 찾지 못했습니다. | 총 소요 시간: {:.2f}초'.format(elapsed))

    return found_password


if __name__ == '__main__':
    # 기본 실행 (단일 프로세스 순서 최적화): unlock_zip(ZIP_FILE)
    # unlock_zip(ZIP_FILE)

    # 보너스 실행 (멀티프로세싱 + 순서 최적화): unlock_zip_fast(ZIP_FILE)
    unlock_zip_fast(ZIP_FILE)
