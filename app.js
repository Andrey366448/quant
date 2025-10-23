const axios = require('axios');
const fs = require('fs');
const path = require('path');


class FullyOptimizedQuantumCircuitProcessor {
    constructor() {
        this.inputDir = path.join(__dirname, 'input');
        this.resultsBaseDir = path.join(__dirname, 'results');
        this.isProcessing = false;
        this.processedFiles = new Set();
        this.loadProcessedFiles();
    }


    loadProcessedFiles() {
        try {
            const processedPath = path.join(this.resultsBaseDir, 'processed_files.json');
            if (fs.existsSync(processedPath)) {
                const data = JSON.parse(fs.readFileSync(processedPath, 'utf8'));
                this.processedFiles = new Set(data.files || []);
            }
        } catch (error) {
            console.log('Не удалось загрузить историю обработанных файлов, начинаем заново');
        }
    }


    saveProcessedFiles() {
        try {
            const processedPath = path.join(this.resultsBaseDir, 'processed_files.json');
            const data = {
                files: Array.from(this.processedFiles),
                timestamp: new Date().toISOString()
            };
            fs.writeFileSync(processedPath, JSON.stringify(data, null, 2));
        } catch (error) {
            console.error('Ошибка сохранения истории файлов:', error.message);
        }
    }


    // Функция для создания пар из массива графов
    createPairs(graphFolders) {
        const pairs = [];
        for (let i = 0; i < graphFolders.length; i += 2) {
            if (i + 1 < graphFolders.length) {
                pairs.push([graphFolders[i], graphFolders[i + 1]]);
            } else {
                pairs.push([graphFolders[i]]); // Последний элемент если нечетное количество
            }
        }
        return pairs;
    }


    async startMonitoring() {
        console.log('🚀 Запуск полностью оптимизированного мониторинга с попарной обработкой ВСЕХ графов...');
        console.log('📁 Мониторинг папки:', this.inputDir);
        console.log('💾 Результаты в:', this.resultsBaseDir);
        console.log('⚡ Стратегия: ВСЕ графы обрабатываются попарно параллельно');
        
        // Создание папок при первом запуске
        if (!fs.existsSync(this.inputDir)) {
            fs.mkdirSync(this.inputDir, { recursive: true });
            console.log('✅ Создана папка input для входных данных');
        }
        if (!fs.existsSync(this.resultsBaseDir)) {
            fs.mkdirSync(this.resultsBaseDir, { recursive: true });
            console.log('✅ Создана папка quantum_results для результатов');
        }


        this.isProcessing = true;
        
        // Основной цикл мониторинга с полной попарной обработкой
        while (this.isProcessing) {
            try {
                await this.processAllGraphsInPairs();
                await this.delay(5000); // Проверка каждые 5 секунд
            } catch (error) {
                console.error('❌ Ошибка в основном цикле:', error.message);
                await this.delay(10000); // Пауза при ошибке
            }
        }
    }


    stopMonitoring() {
        console.log('🛑 Остановка полностью оптимизированного мониторинга...');
        this.isProcessing = false;
        this.saveProcessedFiles();
    }


    async processAllGraphsInPairs() {
        try {
            if (!fs.existsSync(this.inputDir)) {
                return;
            }

            // Получаем все доступные графы и сортируем их
            const availableGraphs = fs.readdirSync(this.inputDir)
                .filter(item => {
                    const itemPath = path.join(this.inputDir, item);
                    return fs.statSync(itemPath).isDirectory() && item.startsWith('graph_');
                })
                .sort((a, b) => {
                    const numA = parseInt(a.replace('graph_', ''));
                    const numB = parseInt(b.replace('graph_', ''));
                    return numA - numB;
                });

            if (availableGraphs.length === 0) {
                console.log('📭 В папке input нет папок graph_N');
                return;
            }

            console.log(`📊 Найдено графов для обработки: ${availableGraphs.length}`);
            console.log(`📈 Графы: ${availableGraphs.join(', ')}`);

            // Создаем пары из всех доступных графов
            const graphPairs = this.createPairs(availableGraphs);
            console.log(`🔗 Создано пар для параллельной обработки: ${graphPairs.length}`);
            
            // Выводим информацию о парах
            graphPairs.forEach((pair, index) => {
                if (pair.length === 2) {
                    console.log(`   Пара ${index + 1}: ${pair[0]} + ${pair[1]} (параллельно)`);
                } else {
                    console.log(`   Пара ${index + 1}: ${pair[0]} (одиночно)`);
                }
            });

            let totalProcessed = 0;

            // Обрабатываем каждую пару графов
            for (let pairIndex = 0; pairIndex < graphPairs.length; pairIndex++) {
                const currentPair = graphPairs[pairIndex];
                console.log(`\n🔄 Обработка пары ${pairIndex + 1}/${graphPairs.length}: [${currentPair.join(', ')}]`);

                const parallelTasks = currentPair.map(graphName => 
                    this.processGraphFolder(graphName)
                );

                // Ждем завершения обработки текущей пары
                const pairResults = await Promise.all(parallelTasks);
                const pairProcessed = pairResults.reduce((sum, count) => sum + count, 0);
                totalProcessed += pairProcessed;

                if (pairProcessed > 0) {
                    console.log(`✅ Пара ${pairIndex + 1} завершена: обработано ${pairProcessed} файлов`);
                    this.saveProcessedFiles();
                } else {
                    console.log(`⏭️  Пара ${pairIndex + 1} пропущена: нет новых файлов для обработки`);
                }

                // Небольшая задержка между парами для стабильности сервера
                if (pairIndex < graphPairs.length - 1) {
                    await this.delay(2000);
                }
            }

            if (totalProcessed > 0) {
                console.log(`\n🎯 ИТОГО обработано файлов в этой итерации: ${totalProcessed}`);
                console.log(`⚡ Использовано пар для ускорения: ${graphPairs.length}`);
            }

        } catch (error) {
            console.error('❌ Ошибка при попарной обработке графов:', error.message);
        }
    }


    async processGraphFolder(graphFolder) {
        const graphPath = path.join(this.inputDir, graphFolder);
        let processedCount = 0;

        try {
            // Создание папки для результатов этого графа
            const graphResultsDir = path.join(this.resultsBaseDir, graphFolder);
            if (!fs.existsSync(graphResultsDir)) {
                fs.mkdirSync(graphResultsDir, { recursive: true });
            }

            // Чтение всех JSON файлов в папке графа
            const jsonFiles = fs.readdirSync(graphPath)
                .filter(file => file.endsWith('.json'))
                .sort();

            if (jsonFiles.length === 0) {
                console.log(`📭 [${graphFolder}] Нет JSON файлов`);
                return 0;
            }

            console.log(`📊 [${graphFolder}] Найдено ${jsonFiles.length} файлов`);

            for (const jsonFile of jsonFiles) {
                const fileKey = `${graphFolder}/${jsonFile}`;
                
                // Пропускаем уже обработанные файлы
                if (this.processedFiles.has(fileKey)) {
                    continue;
                }

                const success = await this.processFile(graphFolder, jsonFile, graphResultsDir);
                if (success) {
                    this.processedFiles.add(fileKey);
                    processedCount++;
                    
                    // Задержка между запросами чтобы не перегружать сервер
                    await this.delay(1000);
                }
            }

            if (processedCount > 0) {
                console.log(`✅ [${graphFolder}] Завершено: обработано ${processedCount} файлов`);
            }

        } catch (error) {
            console.error(`❌ [${graphFolder}] Ошибка при обработке графа:`, error.message);
        }

        return processedCount;
    }


    async processFile(graphFolder, jsonFile, graphResultsDir) {
        const configPath = path.join(this.inputDir, graphFolder, jsonFile);
        
        try {
            console.log(`🔍 [${graphFolder}] Обработка: ${jsonFile}`);
            
            const circuitData = JSON.parse(fs.readFileSync(configPath, 'utf8'));

            // Настройки API
            const apiUrl = 'https://mireatom.mirea.ru/kraniki/circuit/api';
            const auth = {
                username: 'mirxbo@yandex.ru',
                password: '68ae1805cab0d63b268dbdd40cf41aad'
            };

            const response = await axios.post(apiUrl, circuitData, {
                auth,
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: 15000
            });

            // Создание имени файла результата в формате "Result_graph_*_car_*.json"
            const outputFilename = this.generateResultFilename(graphFolder, jsonFile);
            const outputPath = path.join(graphResultsDir, outputFilename);

            // Обработка ответа
            let resultData;
            if (response.data.data && Array.isArray(response.data.data)) {
                resultData = response.data;
            } else if (response.data.status === true && response.data.data && typeof response.data.data === 'object') {
                resultData = {
                    data: Object.entries(response.data.data).map(([bitstring, value]) => ({
                        bitstring,
                        value
                    }))
                };
            } else {
                throw new Error('Неизвестный формат ответа от сервера');
            }

            // Сохранение файла
            fs.writeFileSync(outputPath, JSON.stringify(resultData, null, 2));
            console.log(`✅ [${graphFolder}] Успех: ${outputFilename}`);

            return true;

        } catch (error) {
            console.error(`❌ [${graphFolder}] Ошибка в файле ${jsonFile}:`, error.message);
            
            if (error.response) {
                console.error(`   HTTP статус: ${error.response.status}`);
                if (error.response.data) {
                    console.error('   Данные ошибки:', JSON.stringify(error.response.data, null, 2));
                }
            }
            
            return false;
        }
    }


    generateResultFilename(graphFolder, originalFilename) {
        // Извлекаем номер графа из названия папки
        const graphMatch = graphFolder.match(/graph_(\d+)/);
        
        if (!graphMatch) {
            // Если имя папки не соответствует формату, используем fallback
            const fileNameWithoutExt = originalFilename.replace('.json', '');
            return `Result_${fileNameWithoutExt}.json`;
        }

        const graphNum = graphMatch[1];
        
        // Извлекаем номер car из имени файла
        const carMatch = originalFilename.match(/_car_(\d+)\.json$/);
        
        if (carMatch) {
            const carNum = carMatch[1];
            return `Result_graph_${graphNum}_car_${carNum}.json`;
        } else {
            // Если в имени файла нет номера car, используем только номер графа
            const fileNameWithoutExt = originalFilename.replace('.json', '');
            return `Result_graph_${graphNum}_${fileNameWithoutExt}.json`;
        }
    }


    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }


    getStatus() {
        const graphFolders = fs.existsSync(this.inputDir) ? 
            fs.readdirSync(this.inputDir).filter(item => {
                const itemPath = path.join(this.inputDir, item);
                return fs.statSync(itemPath).isDirectory() && item.startsWith('graph_');
            }).length : 0;

        const pairs = this.createPairs(
            Array.from({length: graphFolders}, (_, i) => `graph_${i}`)
        );

        return {
            isMonitoring: this.isProcessing,
            processedFilesCount: this.processedFiles.size,
            graphFoldersCount: graphFolders,
            estimatedPairs: pairs.length,
            inputDir: this.inputDir,
            resultsDir: this.resultsBaseDir,
            optimizationType: 'Полная попарная параллельность ВСЕХ графов'
        };
    }


    // Метод для ручной обработки всех файлов (однократно) с полной попарностью
    async processOnce() {
        console.log('🔧 Запуск полностью оптимизированной однократной обработки...');
        await this.processAllGraphsInPairs();
        this.saveProcessedFiles();
        console.log('✅ Полностью оптимизированная однократная обработка завершена');
    }


    // Дополнительный метод для получения информации о текущих парах
    getCurrentPairs() {
        if (!fs.existsSync(this.inputDir)) {
            return [];
        }

        const availableGraphs = fs.readdirSync(this.inputDir)
            .filter(item => {
                const itemPath = path.join(this.inputDir, item);
                return fs.statSync(itemPath).isDirectory() && item.startsWith('graph_');
            })
            .sort((a, b) => {
                const numA = parseInt(a.replace('graph_', ''));
                const numB = parseInt(b.replace('graph_', ''));
                return numA - numB;
            });

        return this.createPairs(availableGraphs);
    }


    // Метод для демонстрации стратегии обработки
    showProcessingStrategy() {
        const pairs = this.getCurrentPairs();
        
        console.log('\n🎯 СТРАТЕГИЯ ОБРАБОТКИ:');
        console.log('=' .repeat(50));
        
        if (pairs.length === 0) {
            console.log('❌ Нет графов для обработки');
            return;
        }

        pairs.forEach((pair, index) => {
            const pairNumber = index + 1;
            if (pair.length === 2) {
                console.log(`📌 Этап ${pairNumber}: ${pair[0]} ⟷ ${pair[1]} (параллельно)`);
            } else {
                console.log(`📌 Этап ${pairNumber}: ${pair[0]} (одиночно)`);
            }
        });
        
        console.log('=' .repeat(50));
        console.log(`⚡ Всего этапов обработки: ${pairs.length}`);
        console.log(`🚀 Ускорение: до ${Math.ceil(pairs.reduce((acc, pair) => acc + pair.length, 0) / pairs.length)}x`);
        console.log('');
    }
}


// Создание и настройка полностью оптимизированного процессора
const processor = new FullyOptimizedQuantumCircuitProcessor();


// Обработка сигналов завершения
process.on('SIGINT', () => {
    console.log('\n🛑 Получен SIGINT, останавливаем полную оптимизацию...');
    processor.stopMonitoring();
    process.exit(0);
});


process.on('SIGTERM', () => {
    console.log('\n🛑 Получен SIGTERM, останавливаем полную оптимизацию...');
    processor.stopMonitoring();
    process.exit(0);
});


// Экспорт для использования как модуля
module.exports = processor;


// Автозапуск при прямом запуске файла
if (require.main === module) {
    console.log('🎯 Запуск Fully Optimized Quantum Circuit Processor');
    console.log('⚡ МАКСИМАЛЬНАЯ ОПТИМИЗАЦИЯ: Все графы обрабатываются попарно');
    console.log('💡 Для остановки нажмите Ctrl+C');
    console.log('');
    
    // Показываем стратегию обработки
    processor.showProcessingStrategy();
    
    console.log('📁 Структура папок:');
    console.log('   input/');
    console.log('   ├── graph_0/ ← Пара 1 (параллельно)');
    console.log('   ├── graph_1/ ← Пара 1 (параллельно)');
    console.log('   ├── graph_2/ ← Пара 2 (параллельно)');
    console.log('   ├── graph_3/ ← Пара 2 (параллельно)');
    console.log('   ├── graph_4/ ← Пара 3 (параллельно)');
    console.log('   └── graph_5/ ← Пара 3 (параллельно)');
    console.log('');
    console.log('🚀 Преимущества полной оптимизации:');
    console.log('   • МАКСИМАЛЬНАЯ параллельность - все графы в парах');
    console.log('   • Автоматическое создание пар из любого количества графов');
    console.log('   • Ускорение обработки до 2x для каждой пары');
    console.log('   • Обработка нечетного количества графов');
    console.log('   • Детальное логирование прогресса по парам');
    console.log('   • Контролируемая нагрузка на сервер');
    console.log('');
    
    processor.startMonitoring().catch(error => {
        console.error('💥 Фатальная ошибка:', error);
        process.exit(1);
    });
}