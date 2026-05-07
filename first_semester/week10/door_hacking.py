import itertools
import multiprocessing
import os
import string
import time
import zipfile
import zlib


ZIP_FILE = 'emergency_storage_key.zip'
PASSWORD_FILE = 'key.txt'
CHARSET = string.ascii_lowercase + string.digits
PASSWORD_LENGTH = 6
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
PRIORITY_WORDS = (
    'mars',
    'door',
    'safe',
    'lock',
    'key',
    'pass',
    'code',
    'hint',
    'open',
    'star',
)


def get_target_info(zf):
    file_infos = [info for info in zf.infolist() if not info.is_dir()]
    if not file_infos:
        raise ValueError('ZIP 파일에 확인할 파일이 없습니다.')
    return min(file_infos, key=lambda info: info.file_size)


def save_password(password):
    try:
        with open(PASSWORD_FILE, 'w', encoding='utf-8') as file:
            file.write(password)
        print(f'암호가 {PASSWORD_FILE}에 저장되었습니다.')
    except OSError as error:
        print(f'파일 저장 중 오류가 발생했습니다: {error}')


def extract_zip(zip_filepath, password):
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zf:
            for member in zf.infolist():
                member_path = os.path.abspath(os.path.join(OUTPUT_DIR, member.filename))
                if os.path.commonpath([OUTPUT_DIR, member_path]) != OUTPUT_DIR:
                    raise ValueError(f'안전하지 않은 경로가 포함되어 있습니다: {member.filename}')
            zf.extractall(path=OUTPUT_DIR, pwd=password.encode('utf-8'))
        print(f'압축 해제 결과가 {OUTPUT_DIR}에 저장되었습니다.')
    except (FileNotFoundError, PermissionError, OSError, ValueError, RuntimeError, zipfile.BadZipFile, zlib.error) as error:
        print(f'압축 해제 중 오류가 발생했습니다: {error}')


def is_password_correct(zf, target_info, password):
    try:
        with zf.open(target_info, pwd=password.encode('utf-8')) as file:
            while file.read(8192):
                pass
        return True
    except (RuntimeError, zipfile.BadZipFile, zlib.error):
        return False


def generate_priority_candidates():
    seen = set()

    for word in PRIORITY_WORDS:
        if len(word) == PASSWORD_LENGTH and word not in seen:
            seen.add(word)
            yield word

    for word in PRIORITY_WORDS:
        remain = PASSWORD_LENGTH - len(word)
        if remain <= 0:
            continue

        for suffix in itertools.product(string.digits, repeat=remain):
            candidate = word + ''.join(suffix)
            if candidate not in seen:
                seen.add(candidate)
                yield candidate

        for prefix in itertools.product(string.digits, repeat=remain):
            candidate = ''.join(prefix) + word
            if candidate not in seen:
                seen.add(candidate)
                yield candidate

    for word in PRIORITY_WORDS:
        remain = PASSWORD_LENGTH - len(word)
        if remain != 1:
            continue

        for suffix in string.ascii_lowercase:
            candidate = word + suffix
            if candidate not in seen:
                seen.add(candidate)
                yield candidate

        for prefix in string.ascii_lowercase:
            candidate = prefix + word
            if candidate not in seen:
                seen.add(candidate)
                yield candidate


def try_priority_passwords(zip_filepath):
    attempts = 0

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zf:
            target_info = get_target_info(zf)

            for candidate in generate_priority_candidates():
                attempts += 1
                if is_password_correct(zf, target_info, candidate):
                    return candidate, attempts
    except (FileNotFoundError, PermissionError, OSError, ValueError) as error:
        return f'error:{error}', attempts

    return None, attempts


def check_password_chunk(args):
    zip_filepath, first_char, stop_event = args
    attempts = 0

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zf:
            target_info = get_target_info(zf)

            for guess_tuple in itertools.product(CHARSET, repeat=PASSWORD_LENGTH - 1):
                if stop_event.is_set():
                    return None, attempts

                attempts += 1
                guess = first_char + ''.join(guess_tuple)
                if is_password_correct(zf, target_info, guess):
                    stop_event.set()
                    return guess, attempts
    except (FileNotFoundError, PermissionError, OSError, ValueError) as error:
        return f'error:{error}', attempts

    return None, attempts


def unlock_zip(zip_filepath=ZIP_FILE):
    start_time = time.time()
    print(f'탐색 시작 시간: {time.strftime("%Y-%m-%d %H:%M:%S")}')

    if not os.path.exists(zip_filepath):
        print(f'오류: {zip_filepath} 파일을 찾을 수 없습니다.')
        return None

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zf:
            get_target_info(zf)
    except (FileNotFoundError, PermissionError, OSError, ValueError) as error:
        print(f'오류: ZIP 파일을 열 수 없습니다: {error}')
        return None

    manager = multiprocessing.Manager()
    stop_event = manager.Event()
    tasks = [(zip_filepath, char, stop_event) for char in CHARSET]
    cpu_cores = multiprocessing.cpu_count()

    print(f'활성화된 코어 수: {cpu_cores}개')
    print('우선 키워드 기반 탐색을 시작합니다...')

    total_attempts = 0
    found_password = None

    priority_result, priority_attempts = try_priority_passwords(zip_filepath)
    total_attempts += priority_attempts

    if isinstance(priority_result, str) and priority_result.startswith('error:'):
        print(priority_result[6:])
        return None

    if priority_result:
        found_password = priority_result
    else:
        print('키워드 우선 탐색 실패, 전체 병렬 탐색으로 전환합니다...')

        with multiprocessing.Pool(processes=cpu_cores) as pool:
            for result_guess, result_attempts in pool.imap_unordered(check_password_chunk, tasks):
                total_attempts += result_attempts

                if isinstance(result_guess, str) and result_guess.startswith('error:'):
                    print(result_guess[6:])
                    pool.terminate()
                    break

                if result_guess:
                    found_password = result_guess
                    pool.terminate()
                    break

    elapsed = time.time() - start_time

    if found_password:
        print('[성공] 암호를 찾았습니다!')
        print(f'찾은 암호: {found_password}')
        print(f'총 반복 횟수: {total_attempts}회')
        print(f'진행 시간: {elapsed:.2f}초')
        save_password(found_password)
        extract_zip(zip_filepath, found_password)
        return found_password

    print('모든 조합을 시도했지만 암호를 찾지 못했습니다.')
    print(f'진행 시간: {elapsed:.2f}초')
    return None


if __name__ == '__main__':
    unlock_zip()
