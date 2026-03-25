import csv
import pickle


def parse_number(value):
    """문자열을 float로 변환한다. 변환 불가 시 None을 반환한다."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def compute_danger_score(flammability, specific_gravity):
    """인화성과 비중을 곱해 복합 위험도 점수를 계산한다.
    비중이 없을 경우(Various) 중립값 1.0을 사용한다.
    """
    sg = specific_gravity if specific_gravity is not None else 1.0
    return round(flammability * sg, 4)


def read_csv(filename):
    """CSV 파일을 읽어 헤더와 데이터 리스트로 반환한다.
    각 행은 [Substance, Weight, Specific Gravity, Strength,
              Flammability, Danger Score] 형태이다.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader) + ['Danger Score']
            data = []
            for row in reader:
                if not row:
                    continue
                try:
                    row[4] = float(row[4])
                except (ValueError, IndexError):
                    continue
                sg = parse_number(row[2])
                row.append(compute_danger_score(row[4], sg))
                data.append(row)
        return header, data
    except FileNotFoundError:
        print(f'오류: 파일을 찾을 수 없습니다 - {filename}')
    except PermissionError:
        print(f'오류: 파일 접근 권한이 없습니다 - {filename}')
    return None, None


def print_csv(header, data):
    """CSV 데이터를 화면에 출력한다."""
    print(','.join(header))
    for row in data:
        print(','.join(str(v) for v in row))


def sort_by_danger_score(data):
    """복합 위험도 점수(Danger Score) 기준 내림차순으로 정렬한 새 리스트를 반환한다."""
    return sorted(data, key=lambda x: x[5], reverse=True)


def filter_danger(data, threshold=0.7):
    """인화성 지수가 threshold 이상인 항목만 필터링해 반환한다."""
    return [row for row in data if row[4] >= threshold]


def save_csv(filename, header, data):
    """데이터를 CSV 파일로 저장한다."""
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
        print(f'저장 완료: {filename}')
    except PermissionError:
        print(f'오류: 파일 저장 권한이 없습니다 - {filename}')


def save_bin(filename, data):
    """데이터를 이진 파일(pickle)로 저장한다."""
    try:
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print(f'이진 파일 저장 완료: {filename}')
    except PermissionError:
        print(f'오류: 파일 저장 권한이 없습니다 - {filename}')


def load_bin(filename):
    """이진 파일(pickle)을 읽어 데이터를 반환한다."""
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print(f'오류: 파일을 찾을 수 없습니다 - {filename}')
    except PermissionError:
        print(f'오류: 파일 접근 권한이 없습니다 - {filename}')
    return None


def main():
    csv_file = 'Mars_Base_Inventory_List.csv'
    danger_file = 'Mars_Base_Inventory_danger.csv'
    bin_file = 'Mars_Base_Inventory_List.bin'

    # CSV 읽기 및 출력
    header, data = read_csv(csv_file)
    if data is None:
        return

    print('=== 전체 화물 목록 ===')
    print_csv(header, data)

    # 복합 위험도 점수 기준 정렬
    sorted_data = sort_by_danger_score(data)
    print('\n=== 복합 위험도(인화성 × 비중) 높은 순 정렬 ===')
    print_csv(header, sorted_data)

    # 인화성 0.7 이상 필터링 및 출력
    danger_data = filter_danger(sorted_data)
    print('\n=== 인화성 0.7 이상 위험 물질 ===')
    print_csv(header, danger_data)

    # 위험 물질 CSV 저장
    save_csv(danger_file, header, danger_data)

    # 보너스: 이진 파일 저장
    save_bin(bin_file, sorted_data)

    # 보너스: 이진 파일 읽기 및 출력
    bin_data = load_bin(bin_file)
    if bin_data:
        print('\n=== 이진 파일에서 읽은 데이터 ===')
        print_csv(header, bin_data)


if __name__ == '__main__':
    main()
