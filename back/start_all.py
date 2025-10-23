import subprocess
import sys
import os
import glob
import signal
import time

# Константа - максимальное количество файлов
MAX_FILES_COUNT = 10

def count_result_files():
    """
    Подсчитывает количество файлов с паттерном post_processed_routes_graph_*.json в директории results
    """
    pattern = "results/post_processed_routes_graph_*.json"
    files = glob.glob(pattern)
    return len(files)


def monitor_and_terminate(processes_to_monitor, check_interval=5):
    """
    Мониторит количество файлов и завершает указанные процессы при превышении лимита
    
    Args:
        processes_to_monitor: список процессов для мониторинга
        check_interval: интервал проверки в секундах
    """
    while True:
        # Проверяем, живы ли ещё процессы
        active_processes = [p for p in processes_to_monitor if p.poll() is None]
        
        if not active_processes:
            print("Все мониторируемые процессы завершены")
            break
        
        # Считаем файлы
        file_count = count_result_files()
        print(f"Текущее количество файлов: {file_count}/{MAX_FILES_COUNT}")
        
        if file_count > MAX_FILES_COUNT:
            print(f"\n⚠ Превышен лимит файлов ({file_count} > {MAX_FILES_COUNT})")
            print("Завершаем процессы script3.py, script4.py и script.js...")
            
            for process in active_processes:
                try:
                    # Пытаемся корректно завершить процесс
                    process.terminate()
                    print(f"✓ Процесс {process.pid} получил сигнал завершения")
                except Exception as e:
                    print(f"✗ Ошибка при завершении процесса {process.pid}: {e}")
            
            # Даём процессам время на корректное завершение
            time.sleep(2)
            
            # Принудительное завершение, если процесс не завершился
            for process in active_processes:
                if process.poll() is None:
                    try:
                        process.kill()
                        print(f"✓ Процесс {process.pid} принудительно завершён")
                    except Exception as e:
                        print(f"✗ Ошибка при принудительном завершении {process.pid}: {e}")
            
            break
        
        time.sleep(check_interval)


def run_scripts():
    """
    Функция для последовательного запуска четырёх Python скриптов и одного JS скрипта
    """
    
    # Пути к скриптам
    python_script_1 = "prep_csv.py"
    python_script_2 = "quant.py"
    python_script_3 = "p_quntun.py"
    python_script_4 = "finily_csv.py"
    js_script = "app.js"
    
    try:
        # Запуск первых двух Python скриптов последовательно
        print(f"Запуск {python_script_1}...")
        result1 = subprocess.run(
            [sys.executable, python_script_1],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {python_script_1} выполнен успешно")
        if result1.stdout:
            print(f"Вывод: {result1.stdout}")
        print()
        
        print(f"Запуск {python_script_2}...")
        result2 = subprocess.run(
            [sys.executable, python_script_2],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {python_script_2} выполнен успешно")
        if result2.stdout:
            print(f"Вывод: {result2.stdout}")
        print()
        
        # Запуск скриптов 3, 4 и JS с мониторингом
        print(f"Запуск {python_script_3} (с мониторингом)...")
        process3 = subprocess.Popen(
            [sys.executable, python_script_3],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Запуск {python_script_4} (с мониторингом)...")
        process4 = subprocess.Popen(
            [sys.executable, python_script_4],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Запуск {js_script} (с мониторингом)...")
        process_js = subprocess.Popen(
            ["node", js_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Список процессов для мониторинга
        monitored_processes = [process3, process4, process_js]
        
        print("\n📊 Запущен мониторинг количества файлов...")
        print(f"Лимит: {MAX_FILES_COUNT} файлов\n")
        
        # Запуск мониторинга
        monitor_and_terminate(monitored_processes, check_interval=5)
        
        # Получение результатов завершённых процессов
        stdout3, stderr3 = process3.communicate()
        stdout4, stderr4 = process4.communicate()
        stdout_js, stderr_js = process_js.communicate()
        
        print("\n--- Результаты выполнения ---")
        
        if process3.returncode == 0:
            print(f"✓ {python_script_3} завершён успешно")
        else:
            print(f"⚠ {python_script_3} завершён с кодом {process3.returncode}")
        if stdout3:
            print(f"Вывод: {stdout3}")
        if stderr3:
            print(f"Ошибки: {stderr3}")
        print()
        
        if process4.returncode == 0:
            print(f"✓ {python_script_4} завершён успешно")
        else:
            print(f"⚠ {python_script_4} завершён с кодом {process4.returncode}")
        if stdout4:
            print(f"Вывод: {stdout4}")
        if stderr4:
            print(f"Ошибки: {stderr4}")
        print()
        
        if process_js.returncode == 0:
            print(f"✓ {js_script} завершён успешно")
        else:
            print(f"⚠ {js_script} завершён с кодом {process_js.returncode}")
        if stdout_js:
            print(f"Вывод: {stdout_js}")
        if stderr_js:
            print(f"Ошибки: {stderr_js}")
        
        print("\n✓ Все скрипты завершены!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Ошибка при выполнении скрипта:")
        print(f"Код возврата: {e.returncode}")
        print(f"Ошибка: {e.stderr}")
        return False
    except FileNotFoundError as e:
        print(f"\n✗ Файл не найден или Node.js не установлен: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠ Получен сигнал прерывания (Ctrl+C)")
        print("Завершаем все процессы...")
        for p in [process3, process4, process_js]:
            if p.poll() is None:
                p.terminate()
        return False
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")
        return False


def run_scripts_parallel():
    """
    Функция для параллельного запуска четырёх Python скриптов и одного JS скрипта
    с мониторингом файлов
    """
    import concurrent.futures
    import threading
    
    python_script_1 = "prep_csv.py"
    python_script_2 = "quant.py"
    js_script = "app.js"
    python_script_3 = "p_quntun.py"
    python_script_4 = "finily_csv.py"
    
    
    # Словарь для хранения процессов, которые нужно мониторить
    monitored_processes = {}
    stop_monitoring = threading.Event()
    
    def monitor_files_parallel():
        """Мониторит файлы в отдельном потоке для параллельного режима"""
        while not stop_monitoring.is_set():
            file_count = count_result_files()
            print(f"Текущее количество файлов: {file_count}/{MAX_FILES_COUNT}")
            
            if file_count > MAX_FILES_COUNT:
                print(f"\n⚠ Превышен лимит файлов ({file_count} > {MAX_FILES_COUNT})")
                print("Завершаем процессы script3.py, script4.py и script.js...")
                
                for script_name, process in monitored_processes.items():
                    if process and process.poll() is None:
                        try:
                            process.terminate()
                            print(f"✓ Процесс {script_name} (PID: {process.pid}) завершён")
                        except Exception as e:
                            print(f"✗ Ошибка при завершении {script_name}: {e}")
                
                stop_monitoring.set()
                break
            
            time.sleep(5)
    
    def run_python_script(script_path):
        if script_path in [python_script_3, python_script_4]:
            # Для мониторируемых скриптов используем Popen
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            monitored_processes[script_path] = process
            stdout, stderr = process.communicate()
            return script_path, process.returncode, stdout, stderr
        else:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True
            )
            return script_path, result.returncode, result.stdout, result.stderr
    
    def run_js_script(script_path):
        process = subprocess.Popen(
            ["node", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        monitored_processes[script_path] = process
        stdout, stderr = process.communicate()
        return script_path, process.returncode, stdout, stderr
    
    try:
        # Запуск мониторинга в отдельном потоке
        monitor_thread = threading.Thread(target=monitor_files_parallel, daemon=True)
        monitor_thread.start()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Запуск всех скриптов параллельно
            futures = [
                executor.submit(run_python_script, python_script_1),
                executor.submit(run_python_script, python_script_2),
                executor.submit(run_python_script, python_script_3),
                executor.submit(run_python_script, python_script_4),
                executor.submit(run_js_script, js_script)
            ]
            
            # Получение результатов
            for future in concurrent.futures.as_completed(futures):
                script_name, returncode, stdout, stderr = future.result()
                if returncode == 0:
                    print(f"✓ {script_name} выполнен успешно")
                    if stdout:
                        print(f"Вывод: {stdout}")
                else:
                    print(f"⚠ {script_name} завершился с кодом {returncode}")
                    if stderr:
                        print(f"Ошибка: {stderr}")
                print()
        
        stop_monitoring.set()
        monitor_thread.join(timeout=1)
        
        print("✓ Все скрипты завершены!")
        return True
        
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        stop_monitoring.set()
        return False


if __name__ == "__main__":
    # Создаём директорию results, если её нет
    os.makedirs("results", exist_ok=True)
    
    print(f"📁 Лимит файлов установлен: {MAX_FILES_COUNT}")
    print(f"📂 Директория мониторинга: results/")
    print(f"🔍 Паттерн файлов: post_processed_routes_graph_*.json\n")
    
    # Выберите нужный вариант:
    
    # Последовательный запуск (скрипты 1-2 последовательно, затем 3-4 и JS с мониторингом)
    run_scripts()
    
    # Или параллельный запуск (все одновременно с мониторингом)
    # run_scripts_parallel()
